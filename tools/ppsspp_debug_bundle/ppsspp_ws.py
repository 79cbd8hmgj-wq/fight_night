#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time
from collections.abc import Mapping
from typing import Any

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 56244
_PATH = "/debugger"


class WebSocketError(RuntimeError):
    """Raised when the local PPSSPP WebSocket transport is invalid."""


def encode_client_text_frame(text: str, *, mask_key: bytes | None = None) -> bytes:
    return _encode_client_frame(text.encode("utf-8"), opcode=0x1, mask_key=mask_key)


def _encode_client_frame(
    payload: bytes,
    *,
    opcode: int,
    mask_key: bytes | None = None,
) -> bytes:
    key = os.urandom(4) if mask_key is None else mask_key
    if len(key) != 4:
        raise ValueError("WebSocket mask key must be exactly four bytes")
    first = 0x80 | opcode
    length = len(payload)
    if length < 126:
        header = bytes((first, 0x80 | length))
    elif length <= 0xFFFF:
        header = bytes((first, 0x80 | 126)) + struct.pack("!H", length)
    else:
        header = bytes((first, 0x80 | 127)) + struct.pack("!Q", length)
    masked = bytes(value ^ key[index % 4] for index, value in enumerate(payload))
    return header + key + masked


def _recv_exact(connection: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = connection.recv(remaining)
        if not chunk:
            raise WebSocketError("WebSocket connection closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_http_headers(connection: socket.socket) -> bytes:
    data = bytearray()
    while b"\r\n\r\n" not in data:
        chunk = connection.recv(4096)
        if not chunk:
            raise WebSocketError("remote debugger closed during WebSocket handshake")
        data.extend(chunk)
        if len(data) > 65536:
            raise WebSocketError("WebSocket handshake headers are too large")
    return bytes(data)


def _connect(host: str, port: int, timeout: float) -> socket.socket:
    connection = socket.create_connection((host, port), timeout=timeout)
    connection.settimeout(timeout)
    nonce = base64.b64encode(os.urandom(16)).decode("ascii")
    request = (
        f"GET {_PATH} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {nonce}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    ).encode("ascii")
    connection.sendall(request)
    response = _recv_http_headers(connection)
    header_text = response.decode("iso-8859-1")
    lines = header_text.split("\r\n")
    if not lines or " 101 " not in f" {lines[0]} ":
        connection.close()
        raise WebSocketError(f"unexpected WebSocket status: {lines[0] if lines else ''}")
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.casefold()] = value.strip()
    expected = base64.b64encode(hashlib.sha1((nonce + _GUID).encode("ascii")).digest()).decode(
        "ascii"
    )
    if headers.get("sec-websocket-accept") != expected:
        connection.close()
        raise WebSocketError("WebSocket accept key mismatch")
    return connection


def _receive_frame(connection: socket.socket) -> tuple[int, bytes]:
    first, second = _recv_exact(connection, 2)
    opcode = first & 0x0F
    masked = bool(second & 0x80)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact(connection, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(connection, 8))[0]
    mask_key = _recv_exact(connection, 4) if masked else b""
    payload = _recv_exact(connection, length)
    if masked:
        payload = bytes(
            value ^ mask_key[index % 4] for index, value in enumerate(payload)
        )
    return opcode, payload


def _send_event(
    event: Mapping[str, Any],
    *,
    host: str,
    port: int,
    timeout: float,
    wait_seconds: float,
) -> list[Any]:
    connection = _connect(host, port, timeout)
    try:
        connection.sendall(encode_client_text_frame(json.dumps(event, separators=(",", ":"))))
        deadline = time.monotonic() + wait_seconds
        responses: list[Any] = []
        while time.monotonic() < deadline:
            connection.settimeout(max(0.05, deadline - time.monotonic()))
            try:
                opcode, payload = _receive_frame(connection)
            except TimeoutError:
                break
            except socket.timeout:
                break
            if opcode == 0x8:
                break
            if opcode == 0x9:
                connection.sendall(_encode_client_frame(payload, opcode=0xA))
                continue
            if opcode != 0x1:
                continue
            text = payload.decode("utf-8")
            try:
                responses.append(json.loads(text))
            except json.JSONDecodeError:
                responses.append(text)
        return responses
    finally:
        try:
            connection.sendall(_encode_client_frame(b"", opcode=0x8))
        except OSError:
            pass
        connection.close()


def _parse_value(encoded: str) -> Any:
    try:
        return json.loads(encoded)
    except json.JSONDecodeError:
        return encoded


def _parse_parameters(values: list[str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"parameter must use key=value form: {value}")
        key, encoded = value.split("=", 1)
        if not key:
            raise ValueError("parameter key must be non-empty")
        result[key] = _parse_value(encoded)
    return result


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PPSSPP local WebSocket debugger client")
    parser.add_argument("--host", default=_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=_DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--wait", type=float, default=1.0)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="request game.status and require a response")

    event_parser = subparsers.add_parser("event", help="send one debugger event")
    event_parser.add_argument("event")
    event_parser.add_argument("parameters", nargs="*")

    raw_parser = subparsers.add_parser("raw", help="send one raw JSON object")
    raw_parser.add_argument("payload")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if not (1 <= args.port <= 65535):
        raise SystemExit("port must be between 1 and 65535")
    if args.timeout <= 0 or args.wait < 0:
        raise SystemExit("timeout must be positive and wait must be non-negative")

    if args.command == "health":
        request: Mapping[str, Any] = {"event": "game.status"}
    elif args.command == "event":
        request = {"event": args.event, **_parse_parameters(args.parameters)}
    else:
        decoded = json.loads(args.payload)
        if not isinstance(decoded, Mapping):
            raise SystemExit("raw payload must be a JSON object")
        request = decoded

    try:
        responses = _send_event(
            request,
            host=args.host,
            port=args.port,
            timeout=args.timeout,
            wait_seconds=args.wait,
        )
    except (OSError, WebSocketError, ValueError, json.JSONDecodeError) as exc:
        print(f"PPSSPP debugger request failed: {exc}", file=sys.stderr)
        return 2

    for response in responses:
        print(json.dumps(response, sort_keys=True) if not isinstance(response, str) else response)
    if args.command == "health" and not responses:
        print("PPSSPP debugger connected but game.status returned no response", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

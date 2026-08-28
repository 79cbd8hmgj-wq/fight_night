from __future__ import annotations

import base64
import contextlib
import hashlib
import json
import os
import socket
import struct
from collections import defaultdict, deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
_PATH = "/debugger"
_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}
_PSP_BUTTONS = frozenset(
    {
        "up",
        "down",
        "left",
        "right",
        "cross",
        "circle",
        "square",
        "triangle",
        "start",
        "select",
        "l",
        "r",
    }
)


class PpssppDebuggerError(RuntimeError):
    """Raised when the locked local PPSSPP debugger transport is invalid."""


@dataclass(frozen=True, slots=True)
class DebuggerResponse:
    event: str
    payload: dict[str, object]
    ticket: int | None


def _recv_exact(connection: Any, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        try:
            chunk = connection.recv(remaining)
        except TimeoutError as exc:
            raise PpssppDebuggerError("PPSSPP debugger receive timed out") from exc
        if not chunk:
            raise PpssppDebuggerError("PPSSPP debugger connection closed unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_http_headers(connection: Any) -> bytes:
    data = bytearray()
    while not data.endswith(b"\r\n\r\n"):
        try:
            chunk = connection.recv(1)
        except TimeoutError as exc:
            raise PpssppDebuggerError("PPSSPP debugger handshake timed out") from exc
        if not chunk:
            raise PpssppDebuggerError("PPSSPP debugger closed during WebSocket handshake")
        data.extend(chunk)
        if len(data) > 65536:
            raise PpssppDebuggerError("PPSSPP debugger handshake headers are too large")
    return bytes(data)


def _encode_client_frame(
    payload: bytes,
    *,
    opcode: int,
    mask_key: bytes | None = None,
) -> bytes:
    key = os.urandom(4) if mask_key is None else mask_key
    if len(key) != 4:
        raise PpssppDebuggerError("WebSocket mask key must be four bytes")
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


def _receive_frame(connection: Any) -> tuple[int, bytes]:
    first, second = _recv_exact(connection, 2)
    if not first & 0x80:
        raise PpssppDebuggerError("fragmented PPSSPP WebSocket frames are unsupported")
    opcode = first & 0x0F
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", _recv_exact(connection, 2))[0]
    elif length == 127:
        length = struct.unpack("!Q", _recv_exact(connection, 8))[0]
    mask_key = _recv_exact(connection, 4) if second & 0x80 else b""
    payload = _recv_exact(connection, length)
    if mask_key:
        payload = bytes(
            value ^ mask_key[index % 4] for index, value in enumerate(payload)
        )
    return opcode, payload


def _connect(host: str, port: int, timeout_seconds: float) -> Any:
    try:
        connection = socket.create_connection((host, port), timeout=timeout_seconds)
        connection.settimeout(timeout_seconds)
    except OSError as exc:
        raise PpssppDebuggerError(f"unable to connect to PPSSPP debugger: {exc}") from exc

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
    lines = response.decode("iso-8859-1").split("\r\n")
    if not lines or " 101 " not in f" {lines[0]} ":
        connection.close()
        raise PpssppDebuggerError(
            f"unexpected PPSSPP WebSocket status: {lines[0] if lines else ''}"
        )
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line or ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.casefold()] = value.strip()
    expected = base64.b64encode(
        hashlib.sha1((nonce + _GUID).encode("ascii")).digest()
    ).decode("ascii")
    if headers.get("sec-websocket-accept") != expected:
        connection.close()
        raise PpssppDebuggerError("PPSSPP WebSocket accept key mismatch")
    return connection


class PpssppDebuggerClient:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        timeout_seconds: float = 3.0,
    ) -> None:
        normalized_host = host.casefold()
        if normalized_host not in _LOOPBACK_HOSTS:
            raise PpssppDebuggerError("PPSSPP debugger host must be loopback-only")
        if not 1 <= port <= 65535:
            raise PpssppDebuggerError("PPSSPP debugger port must be between 1 and 65535")
        if timeout_seconds <= 0:
            raise PpssppDebuggerError("PPSSPP debugger timeout must be positive")
        self.host = host
        self.port = port
        self.timeout_seconds = timeout_seconds
        self._connection = _connect(host, port, timeout_seconds)
        self._next_ticket = 1
        self._queued_events: dict[str, deque[dict[str, object]]] = defaultdict(deque)
        self.request("version", name="fnr3-re", version="0.1")
        self.request("client.config.set", acknowledgeDeferred=True)

    def close(self) -> None:
        connection = self._connection
        with contextlib.suppress(OSError):
            connection.sendall(_encode_client_frame(b"", opcode=0x8))
        connection.close()

    def __enter__(self) -> PpssppDebuggerClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _send_json(self, payload: Mapping[str, object]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        try:
            self._connection.sendall(_encode_client_frame(encoded, opcode=0x1))
        except OSError as exc:
            raise PpssppDebuggerError(f"PPSSPP debugger send failed: {exc}") from exc

    def _receive_json(self) -> dict[str, object]:
        while True:
            opcode, payload = _receive_frame(self._connection)
            if opcode == 0x8:
                raise PpssppDebuggerError("PPSSPP debugger connection closed")
            if opcode == 0x9:
                self._connection.sendall(_encode_client_frame(payload, opcode=0xA))
                continue
            if opcode == 0xA:
                continue
            if opcode != 0x1:
                continue
            try:
                decoded: object = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise PpssppDebuggerError("invalid JSON from PPSSPP debugger") from exc
            if not isinstance(decoded, dict):
                raise PpssppDebuggerError("PPSSPP debugger JSON response must be an object")
            return {str(key): value for key, value in decoded.items()}

    def _new_ticket(self) -> int:
        ticket = self._next_ticket
        self._next_ticket += 1
        return ticket

    def send(self, event: str, **params: object) -> int:
        ticket = self._new_ticket()
        self._send_json({"event": event, "ticket": ticket, **params})
        return ticket

    def request(self, event: str, **params: object) -> dict[str, object]:
        ticket = self.send(event, **params)
        while True:
            response = self._receive_json()
            response_event = response.get("event")
            response_ticket = response.get("ticket")
            if response_ticket == ticket:
                if response_event == "error":
                    message = response.get("message", "unknown debugger error")
                    raise PpssppDebuggerError(f"PPSSPP debugger error: {message}")
                return response
            if isinstance(response_event, str) and response_ticket is None:
                self._queued_events[response_event].append(response)

    def wait_for_event(
        self,
        event: str,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, object]:
        queued = self._queued_events[event]
        if queued:
            return queued.popleft()
        if timeout_seconds is not None:
            if timeout_seconds <= 0:
                raise PpssppDebuggerError("event timeout must be positive")
            self._connection.settimeout(timeout_seconds)
        try:
            while True:
                response = self._receive_json()
                response_event = response.get("event")
                if response_event == event:
                    return response
                if isinstance(response_event, str) and response.get("ticket") is None:
                    self._queued_events[response_event].append(response)
        finally:
            if timeout_seconds is not None:
                self._connection.settimeout(self.timeout_seconds)

    def get_registers(self) -> dict[str, int]:
        response = self.request("cpu.getAllRegs")
        categories = response.get("categories")
        if not isinstance(categories, list):
            raise PpssppDebuggerError("cpu.getAllRegs response is missing categories")
        registers: dict[str, int] = {}
        for category in categories:
            if not isinstance(category, dict):
                raise PpssppDebuggerError("invalid cpu.getAllRegs category")
            names = category.get("registerNames")
            values = category.get("uintValues")
            if not isinstance(names, list) or not isinstance(values, list):
                raise PpssppDebuggerError("invalid cpu.getAllRegs register arrays")
            if len(names) != len(values):
                raise PpssppDebuggerError("cpu.getAllRegs register arrays differ in length")
            for name, value in zip(names, values, strict=True):
                if not isinstance(name, str) or not isinstance(value, int):
                    raise PpssppDebuggerError("invalid cpu.getAllRegs register value")
                registers[name] = value
        return registers

    def read_memory(self, address: int, size: int) -> bytes:
        if address < 0 or size <= 0:
            raise PpssppDebuggerError("memory read requires non-negative address and positive size")
        response = self.request("memory.read", address=address, size=size)
        encoded = response.get("base64")
        if not isinstance(encoded, str):
            raise PpssppDebuggerError("memory.read response is missing base64")
        try:
            data = base64.b64decode(encoded, validate=True)
        except ValueError as exc:
            raise PpssppDebuggerError("memory.read returned invalid base64") from exc
        if len(data) != size:
            raise PpssppDebuggerError(
                f"memory.read size mismatch: expected {size}, observed {len(data)}"
            )
        return data

    def add_exec_breakpoint(self, address: int) -> None:
        self.request("cpu.breakpoint.add", address=address, enabled=True, log=False)

    def remove_exec_breakpoint(self, address: int) -> None:
        self.request("cpu.breakpoint.remove", address=address)

    def resume(self) -> int:
        return self.send("cpu.resume")

    def game_status(self) -> dict[str, object]:
        return self.request("game.status")

    def run_until_time(self, relative_us: int) -> int:
        if not isinstance(relative_us, int) or isinstance(relative_us, bool) or relative_us <= 0:
            raise PpssppDebuggerError("relative execution time must be a positive integer")
        return self.send("cpu.runUntilTime", relativeUs=relative_us)

    def press_button(self, button: str, *, duration_frames: int = 1) -> None:
        if button not in _PSP_BUTTONS:
            raise PpssppDebuggerError(f"unsupported PSP button: {button!r}")
        if (
            not isinstance(duration_frames, int)
            or isinstance(duration_frames, bool)
            or duration_frames <= 0
        ):
            raise PpssppDebuggerError("button duration must be a positive frame count")
        self.request("input.buttons.press", button=button, duration=duration_frames)

    def set_analog(self, x: float, y: float) -> None:
        if (
            isinstance(x, bool)
            or isinstance(y, bool)
            or not isinstance(x, (int, float))
            or not isinstance(y, (int, float))
            or not -1.0 <= x <= 1.0
            or not -1.0 <= y <= 1.0
        ):
            raise PpssppDebuggerError("analog values must be numeric values in [-1.0, 1.0]")
        self.request("input.analog.send", x=float(x), y=float(y), stick="left")

    def backtrace(self) -> tuple[int, ...]:
        response = self.request("hle.backtrace")
        frames = response.get("frames")
        if not isinstance(frames, list):
            raise PpssppDebuggerError("hle.backtrace response is missing frames")
        pcs: list[int] = []
        for frame in frames:
            if not isinstance(frame, dict) or not isinstance(frame.get("pc"), int):
                raise PpssppDebuggerError("hle.backtrace frame is missing pc")
            pcs.append(frame["pc"])
        return tuple(pcs)

from __future__ import annotations

import base64
import hashlib
import json
import struct

import fnr3_re.ppsspp_debugger as ppsspp_debugger
import pytest

_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def _server_text(payload: dict[str, object]) -> bytes:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    assert len(encoded) < 126
    return bytes((0x81, len(encoded))) + encoded


def _server_frame(opcode: int, payload: bytes) -> bytes:
    assert len(payload) < 126
    return bytes((0x80 | opcode, len(payload))) + payload


def _decode_client_frame(frame: bytes) -> tuple[int, bytes]:
    first, second = frame[:2]
    assert second & 0x80
    length = second & 0x7F
    index = 2
    if length == 126:
        length = struct.unpack("!H", frame[index : index + 2])[0]
        index += 2
    elif length == 127:
        length = struct.unpack("!Q", frame[index : index + 8])[0]
        index += 8
    key = frame[index : index + 4]
    index += 4
    masked = frame[index : index + length]
    payload = bytes(value ^ key[i % 4] for i, value in enumerate(masked))
    return first & 0x0F, payload


class FakeSocket:
    def __init__(self, responses: list[bytes]) -> None:
        self.responses = list(responses)
        self.sent: list[bytes] = []
        self.timeout: float | None = None
        self.closed = False

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, size: int) -> bytes:
        if not self.responses:
            return b""
        current = self.responses[0]
        chunk = current[:size]
        rest = current[size:]
        if rest:
            self.responses[0] = rest
        else:
            self.responses.pop(0)
        return chunk

    def close(self) -> None:
        self.closed = True


def _handshake_response(nonce: bytes = b"0123456789abcdef") -> bytes:
    key = base64.b64encode(nonce).decode("ascii")
    accept = base64.b64encode(
        hashlib.sha1((key + _GUID).encode("ascii")).digest()
    ).decode("ascii")
    return (
        "HTTP/1.1 101 Switching Protocols\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
    ).encode("ascii")


def _client(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[bytes],
) -> tuple[ppsspp_debugger.PpssppDebuggerClient, FakeSocket]:
    socket = FakeSocket([_handshake_response(), *responses])
    monkeypatch.setattr(ppsspp_debugger.os, "urandom", lambda size: b"0123456789abcdef"[:size])
    monkeypatch.setattr(
        ppsspp_debugger.socket,
        "create_connection",
        lambda address, timeout: socket,
    )
    return ppsspp_debugger.PpssppDebuggerClient(
        "127.0.0.1", 56244, timeout_seconds=1.5
    ), socket


def test_rejects_nonloopback_host_before_connection() -> None:
    with pytest.raises(ppsspp_debugger.PpssppDebuggerError, match="loopback"):
        ppsspp_debugger.PpssppDebuggerClient("192.0.2.8", 56244)


def test_connects_to_debugger_path_and_sends_masked_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, socket = _client(
        monkeypatch,
        [
            _server_text({"event": "version", "ticket": 1, "name": "PPSSPP"}),
            _server_text({"event": "client.config.set", "ticket": 2}),
            _server_text({"event": "game.status", "ticket": 3, "game": "running"}),
        ],
    )

    response = client.request("game.status")

    handshake = socket.sent[0].decode("ascii")
    assert handshake.startswith("GET /debugger HTTP/1.1\r\n")
    assert "Host: 127.0.0.1:56244\r\n" in handshake
    assert "Sec-WebSocket-Protocol" not in handshake

    opcode, payload = _decode_client_frame(socket.sent[-1])
    assert opcode == 0x1
    assert json.loads(payload) == {"event": "game.status", "ticket": 3}
    assert response["game"] == "running"


def test_ping_is_answered_and_ticket_correlation_waits_for_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, socket = _client(
        monkeypatch,
        [
            _server_text({"event": "version", "ticket": 1}),
            _server_text({"event": "client.config.set", "ticket": 2}),
            _server_frame(0x9, b"probe"),
            _server_text({"event": "cpu.stepping", "hit": {"address": 0x08804000}}),
            _server_text({"event": "cpu.status", "ticket": 999, "paused": False}),
            _server_text({"event": "cpu.status", "ticket": 3, "paused": True}),
        ],
    )

    result = client.request("cpu.status")

    assert result["paused"] is True
    pong_opcode, pong_payload = _decode_client_frame(socket.sent[-1])
    assert pong_opcode == 0xA
    assert pong_payload == b"probe"
    stepping = client.wait_for_event("cpu.stepping")
    assert stepping["hit"] == {"address": 0x08804000}


def test_matching_debugger_error_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    client, _socket = _client(
        monkeypatch,
        [
            _server_text({"event": "version", "ticket": 1}),
            _server_text({"event": "client.config.set", "ticket": 2}),
            _server_text({"event": "error", "ticket": 3, "message": "bad request"}),
        ],
    )

    with pytest.raises(ppsspp_debugger.PpssppDebuggerError, match="bad request"):
        client.request("cpu.status")


def test_malformed_json_and_disconnect_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    malformed = _server_frame(0x1, b"not-json")
    client, _socket = _client(
        monkeypatch,
        [
            _server_text({"event": "version", "ticket": 1}),
            _server_text({"event": "client.config.set", "ticket": 2}),
            malformed,
        ],
    )
    with pytest.raises(ppsspp_debugger.PpssppDebuggerError, match="JSON"):
        client.request("cpu.status")

    disconnected, _socket = _client(
        monkeypatch,
        [
            _server_text({"event": "version", "ticket": 1}),
            _server_text({"event": "client.config.set", "ticket": 2}),
        ],
    )
    with pytest.raises(ppsspp_debugger.PpssppDebuggerError, match="closed"):
        disconnected.request("cpu.status")


def test_convenience_operations_decode_confirmed_response_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    register_response: dict[str, object] = {
        "event": "cpu.getAllRegs",
        "ticket": 3,
        "categories": [
            {
                "registerNames": ["pc", "a0", "t9"],
                "uintValues": [0x08B44FC0, 7, 0x08B488DC],
            }
        ],
    }
    memory = b"\x10\x20\x30\x40"
    client, _socket = _client(
        monkeypatch,
        [
            _server_text({"event": "version", "ticket": 1}),
            _server_text({"event": "client.config.set", "ticket": 2}),
            _server_text(register_response),
            _server_text(
                {
                    "event": "memory.read",
                    "ticket": 4,
                    "base64": base64.b64encode(memory).decode("ascii"),
                }
            ),
            _server_text({"event": "cpu.breakpoint.add", "ticket": 5}),
            _server_text({"event": "cpu.breakpoint.remove", "ticket": 6}),
            _server_text(
                {
                    "event": "hle.backtrace",
                    "ticket": 8,
                    "walked": True,
                    "frames": [{"pc": 0x08B44FC0}, {"pc": 0x08B488DC}],
                }
            ),
        ],
    )

    assert client.get_registers() == {
        "pc": 0x08B44FC0,
        "a0": 7,
        "t9": 0x08B488DC,
    }
    assert client.read_memory(0x08DBEF10, 4) == memory
    client.add_exec_breakpoint(0x08B44F64)
    client.remove_exec_breakpoint(0x08B44F64)
    resume_ticket = client.resume()
    assert resume_ticket == 7
    assert client.backtrace() == (0x08B44FC0, 0x08B488DC)

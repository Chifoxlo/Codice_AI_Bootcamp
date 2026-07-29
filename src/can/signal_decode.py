"""CAN signal decode: converts raw payload bytes to physical signal values.

Signal specifications are loaded from signals.dbc.json at the repository root.
All arithmetic uses floating-point to preserve fractional physical values.
"""

import json
import os

_DBC_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "signals.dbc.json")

with open(os.path.normpath(_DBC_PATH)) as _f:
    _DBC = json.load(_f)

# Fault codes
FAULT_UNKNOWN_FRAME = "UNKNOWN_FRAME"

# Diagnostics counter — callers may read or reset this list
_faults: list = []


def report_fault(msg_id: int, fault_type: str) -> None:
    """Record a diagnostic fault entry."""
    _faults.append((msg_id, fault_type))


def decode_pedal_position(raw: int) -> float:
    """Return physical pedal-position value for a raw 8-bit integer.

    Factor and offset are taken directly from the DBC so the result is a
    real (float) physical ratio — no int() truncation.
    """
    sig = _DBC["messages"]["0x18F"]["signals"]["PedalPosition"]
    return raw * sig["factor"] + sig["offset"]


class FrameRouter:
    """Route incoming CAN frames to the appropriate decode function."""

    def decode(self, msg_id: int, payload: bytes):
        """Decode *payload* for *msg_id* and return a signal dict, or None.

        Unknown message IDs raise a FAULT_UNKNOWN_FRAME diagnostic and
        return None — they are never silently dropped.
        """
        if msg_id == 0x18F:
            raw = payload[0]
            return {"PedalPosition": decode_pedal_position(raw)}
        else:
            report_fault(msg_id, FAULT_UNKNOWN_FRAME)
            return None

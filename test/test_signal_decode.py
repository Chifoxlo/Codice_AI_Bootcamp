"""Tests for src/can/signal_decode.py."""

import pytest
from src.can.signal_decode import (
    decode_pedal_position,
    FrameRouter,
    report_fault,
    FAULT_UNKNOWN_FRAME,
    _faults,
)


# ---------------------------------------------------------------------------
# decode_pedal_position — fractional float arithmetic (MISRA 10.3 fix)
# ---------------------------------------------------------------------------

class TestDecodePedalPosition:
    def test_raw_zero_returns_zero(self):
        assert decode_pedal_position(0) == pytest.approx(0.0)

    def test_raw_8_returns_half(self):
        # 8 * 0.0625 = 0.5  (was truncated to 0 before fix)
        assert decode_pedal_position(8) == pytest.approx(0.5)

    def test_raw_250_returns_fraction(self):
        # 250 * 0.0625 = 15.625  (was truncated to 15 before fix)
        assert decode_pedal_position(250) == pytest.approx(15.625)

    def test_raw_255_full_scale(self):
        # 255 * 0.0625 = 15.9375
        assert decode_pedal_position(255) == pytest.approx(15.9375)

    def test_result_is_float(self):
        result = decode_pedal_position(8)
        assert isinstance(result, float)

    def test_range_values_preserve_fraction(self):
        # Spot-check several raw values against the DBC formula
        import json, os
        dbc_path = os.path.join(os.path.dirname(__file__), "..", "signals.dbc.json")
        with open(os.path.normpath(dbc_path)) as f:
            dbc = json.load(f)
        sig = dbc["messages"]["0x18F"]["signals"]["PedalPosition"]
        for raw in [1, 4, 16, 64, 128, 200, 255]:
            expected = raw * sig["factor"] + sig["offset"]
            assert decode_pedal_position(raw) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# FrameRouter — unknown-frame fault handling (MISRA 16.4 / BAPS-03 fix)
# ---------------------------------------------------------------------------

class TestFrameRouter:
    def setup_method(self):
        _faults.clear()

    def test_known_frame_returns_dict(self):
        router = FrameRouter()
        result = router.decode(0x18F, bytes([8]))
        assert result is not None
        assert "PedalPosition" in result
        assert result["PedalPosition"] == pytest.approx(0.5)

    def test_unknown_frame_returns_none(self):
        router = FrameRouter()
        result = router.decode(0x999, bytes([0]))
        assert result is None

    def test_unknown_frame_raises_exactly_one_fault(self):
        router = FrameRouter()
        router.decode(0x999, bytes([0]))
        assert len(_faults) == 1

    def test_unknown_frame_fault_contains_correct_id_and_type(self):
        router = FrameRouter()
        router.decode(0xABC, bytes([0]))
        assert _faults[0] == (0xABC, FAULT_UNKNOWN_FRAME)

    def test_multiple_unknown_frames_each_produce_one_fault(self):
        router = FrameRouter()
        router.decode(0x001, bytes([0]))
        router.decode(0x002, bytes([0]))
        assert len(_faults) == 2
        assert _faults[0][0] == 0x001
        assert _faults[1][0] == 0x002

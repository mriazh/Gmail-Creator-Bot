"""
Unit tests untuk RateLimiter.

Requirements: 10.1, 10.3, 10.4
"""

from __future__ import annotations

import sys
import os
from unittest.mock import patch, call

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rate_limiter import RateLimiter


class TestWaitBetweenSessions:
    """Test: jeda selalu dalam rentang [delay_min, delay_max]."""

    def test_delay_within_range(self):
        captured = []

        def mock_countdown(self, seconds, label="Menunggu"):
            captured.append({"seconds": seconds, "label": label})

        with patch.object(RateLimiter, '_countdown', mock_countdown):
            rl = RateLimiter()
            for _ in range(20):
                rl.wait_between_sessions(10, 50)

        # Filter hanya delay "Jeda antar sesi", bukan "Jeda tambahan" (extended break)
        main_delays = [c["seconds"] for c in captured if c["label"] == "Jeda antar sesi"]
        for delay in main_delays:
            assert 10 <= delay <= 50, f"Delay {delay} out of range [10, 50]"

    def test_min_equals_max(self):
        captured = []

        def mock_countdown(self, seconds, label="Menunggu"):
            captured.append(seconds)

        with patch.object(RateLimiter, '_countdown', mock_countdown):
            rl = RateLimiter()
            rl.wait_between_sessions(42, 42)

        assert captured[0] == 42


class TestExtendedBreak:
    """Test: wait_extended_break dipanggil setiap 5 sesi."""

    def test_extended_break_every_5_sessions(self):
        countdown_calls = []

        def mock_countdown(self, seconds, label="Menunggu"):
            countdown_calls.append({"seconds": seconds, "label": label})

        with patch.object(RateLimiter, '_countdown', mock_countdown):
            rl = RateLimiter()
            # Jalankan 5 sesi
            for _ in range(5):
                rl.wait_between_sessions(1, 1)

        # Harus ada 6 countdown calls: 5x regular + 1x extended break
        assert len(countdown_calls) == 6

        # Yang terakhir harus labeled "Jeda tambahan"
        last = countdown_calls[-1]
        assert last["label"] == "Jeda tambahan"
        assert 60 <= last["seconds"] <= 300

    def test_no_extended_break_before_5_sessions(self):
        countdown_calls = []

        def mock_countdown(self, seconds, label="Menunggu"):
            countdown_calls.append({"seconds": seconds, "label": label})

        with patch.object(RateLimiter, '_countdown', mock_countdown):
            rl = RateLimiter()
            for _ in range(4):
                rl.wait_between_sessions(1, 1)

        # Harus ada 4 countdown calls: 4x regular, 0x extended
        assert len(countdown_calls) == 4
        for c in countdown_calls:
            assert c["label"] == "Jeda antar sesi"


class TestRuntimeWarning:
    """Test: peringatan jika bot berjalan >7200 detik."""

    def test_warning_after_2_hours(self, capsys):
        def mock_countdown(self, seconds, label="Menunggu"):
            pass

        with patch.object(RateLimiter, '_countdown', mock_countdown):
            rl = RateLimiter()
            # Simulate 2+ hours elapsed
            rl._start_time -= 7201
            rl.wait_between_sessions(1, 1)

        captured = capsys.readouterr()
        assert "PERINGATAN" in captured.out or "peringatan" in captured.out.lower()

    def test_no_warning_before_2_hours(self, capsys):
        def mock_countdown(self, seconds, label="Menunggu"):
            pass

        with patch.object(RateLimiter, '_countdown', mock_countdown):
            rl = RateLimiter()
            rl.wait_between_sessions(1, 1)

        captured = capsys.readouterr()
        assert "PERINGATAN" not in captured.out

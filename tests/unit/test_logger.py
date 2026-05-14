"""
Unit tests untuk BotLogger.

Mencakup:
- Format output sesuai pola [YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan
- Fallback ke stderr jika file log tidak bisa ditulis
- summary() menampilkan top-3 alasan gagal dengan benar

Requirements: 9.1, 9.6, 9.7
"""

import re
import sys
from collections import Counter
from datetime import datetime
from io import StringIO
from unittest.mock import MagicMock, mock_open, patch

import pytest

# Tambahkan root proyek ke sys.path agar import bot_logger dan models bisa berjalan
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from bot_logger import BotLogger
from models import BatchStats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LOG_PATTERN = re.compile(
    r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[(?:INFO|WARNING|ERROR)\] \[.+\] .+$"
)


def _make_stats(
    total: int = 10,
    successful: int = 7,
    failed: int = 3,
    failure_reasons: Counter | None = None,
) -> BatchStats:
    """Buat objek BatchStats untuk keperluan testing."""
    if failure_reasons is None:
        failure_reasons = Counter()
    return BatchStats(
        total_sessions=total,
        successful=successful,
        failed=failed,
        failure_reasons=failure_reasons,
        start_time=datetime(2024, 1, 1, 0, 0, 0),
        end_time=datetime(2024, 1, 1, 1, 0, 0),
    )


# ---------------------------------------------------------------------------
# Tests: Format output (Requirement 9.1)
# ---------------------------------------------------------------------------


class TestLogFormat:
    """Verifikasi bahwa setiap baris log mengikuti pola yang ditentukan."""

    def test_info_format_matches_pattern(self, tmp_path):
        """Log INFO harus mengikuti pola [YYYY-MM-DD HH:MM:SS] [INFO] [KOMPONEN] pesan."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("TestKomponen", "Pesan info test")

        lines = log_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert LOG_PATTERN.match(lines[0]), f"Format tidak sesuai: {lines[0]!r}"

    def test_warning_format_matches_pattern(self, tmp_path):
        """Log WARNING harus mengikuti pola yang ditentukan."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.warning("TestKomponen", "Pesan warning test")

        lines = log_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert LOG_PATTERN.match(lines[0]), f"Format tidak sesuai: {lines[0]!r}"

    def test_error_format_matches_pattern(self, tmp_path):
        """Log ERROR harus mengikuti pola yang ditentukan."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.error("TestKomponen", "Pesan error test")

        lines = log_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert LOG_PATTERN.match(lines[0]), f"Format tidak sesuai: {lines[0]!r}"

    def test_log_contains_correct_level_info(self, tmp_path):
        """Baris log INFO harus mengandung token [INFO]."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("Komp", "pesan")

        content = log_file.read_text(encoding="utf-8")
        assert "[INFO]" in content

    def test_log_contains_correct_level_warning(self, tmp_path):
        """Baris log WARNING harus mengandung token [WARNING]."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.warning("Komp", "pesan")

        content = log_file.read_text(encoding="utf-8")
        assert "[WARNING]" in content

    def test_log_contains_correct_level_error(self, tmp_path):
        """Baris log ERROR harus mengandung token [ERROR]."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.error("Komp", "pesan")

        content = log_file.read_text(encoding="utf-8")
        assert "[ERROR]" in content

    def test_log_contains_component_name(self, tmp_path):
        """Nama komponen harus muncul di dalam baris log."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("SeedRotator", "pesan")

        content = log_file.read_text(encoding="utf-8")
        assert "[SeedRotator]" in content

    def test_log_contains_message(self, tmp_path):
        """Pesan harus muncul di dalam baris log."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("Komp", "ini adalah pesan unik")

        content = log_file.read_text(encoding="utf-8")
        assert "ini adalah pesan unik" in content

    def test_log_timestamp_is_valid_datetime(self, tmp_path):
        """Timestamp di dalam baris log harus dapat di-parse sebagai datetime."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("Komp", "pesan")

        line = log_file.read_text(encoding="utf-8").strip()
        # Ekstrak timestamp dari dalam kurung siku pertama
        ts_match = re.match(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
        assert ts_match, "Timestamp tidak ditemukan di baris log"
        ts_str = ts_match.group(1)
        # Harus bisa di-parse tanpa exception
        parsed = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        assert isinstance(parsed, datetime)

    def test_multiple_log_entries_each_on_own_line(self, tmp_path):
        """Setiap entri log harus berada pada baris terpisah."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("Komp", "pesan pertama")
        logger.warning("Komp", "pesan kedua")
        logger.error("Komp", "pesan ketiga")

        lines = [l for l in log_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 3
        for line in lines:
            assert LOG_PATTERN.match(line), f"Format tidak sesuai: {line!r}"

    def test_log_appends_to_existing_file(self, tmp_path):
        """Log harus ditulis dalam mode append sehingga entri lama tidak tertimpa."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        logger.info("Komp", "entri pertama")
        logger.info("Komp", "entri kedua")

        lines = [l for l in log_file.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 2


# ---------------------------------------------------------------------------
# Tests: Fallback ke stderr (Requirement 9.7)
# ---------------------------------------------------------------------------


class TestStderrFallback:
    """Verifikasi fallback ke stderr ketika penulisan file gagal."""

    def test_fallback_to_stderr_when_open_raises_permission_error(self, tmp_path):
        """Jika open() melempar PermissionError, log harus dikirim ke stderr."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        captured_stderr = StringIO()
        with patch("builtins.open", side_effect=PermissionError("permission denied")):
            with patch("sys.stderr", captured_stderr):
                logger.info("Komp", "pesan fallback")

        output = captured_stderr.getvalue()
        assert "pesan fallback" in output

    def test_fallback_to_stderr_when_open_raises_oserror(self, tmp_path):
        """Jika open() melempar OSError (misal disk penuh), log harus dikirim ke stderr."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        captured_stderr = StringIO()
        with patch("builtins.open", side_effect=OSError("disk full")):
            with patch("sys.stderr", captured_stderr):
                logger.warning("Komp", "pesan disk penuh")

        output = captured_stderr.getvalue()
        assert "pesan disk penuh" in output

    def test_fallback_stderr_output_still_follows_log_format(self, tmp_path):
        """Output fallback ke stderr harus tetap mengikuti pola format log."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        captured_stderr = StringIO()
        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch("sys.stderr", captured_stderr):
                logger.error("Komp", "error fallback")

        lines = [l for l in captured_stderr.getvalue().splitlines() if l.strip()]
        assert len(lines) >= 1
        assert LOG_PATTERN.match(lines[0]), f"Format fallback tidak sesuai: {lines[0]!r}"

    def test_fallback_does_not_raise_exception(self, tmp_path):
        """Fallback ke stderr tidak boleh melempar exception ke pemanggil."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        with patch("builtins.open", side_effect=PermissionError("denied")):
            with patch("sys.stderr", StringIO()):
                # Tidak boleh ada exception yang muncul
                logger.info("Komp", "pesan aman")
                logger.warning("Komp", "warning aman")
                logger.error("Komp", "error aman")

    def test_no_fallback_when_file_write_succeeds(self, tmp_path):
        """Ketika penulisan file berhasil, stderr tidak boleh menerima output log."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        captured_stderr = StringIO()
        with patch("sys.stderr", captured_stderr):
            logger.info("Komp", "pesan normal")

        # stderr harus kosong (tidak ada fallback)
        assert captured_stderr.getvalue() == ""


# ---------------------------------------------------------------------------
# Tests: summary() top-3 alasan gagal (Requirement 9.6)
# ---------------------------------------------------------------------------


class TestSummary:
    """Verifikasi bahwa summary() menampilkan top-3 alasan gagal dengan benar."""

    def test_summary_shows_top3_failure_reasons(self, tmp_path, capsys):
        """summary() harus menampilkan 3 alasan gagal terbanyak secara berurutan."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        reasons = Counter({
            "CAPTCHA": 10,
            "NETWORK_ERROR": 7,
            "USERNAME_TAKEN": 5,
            "TIMEOUT": 2,
        })
        stats = _make_stats(failure_reasons=reasons)

        logger.summary(stats)

        captured = capsys.readouterr().out
        # Top-3 harus muncul: CAPTCHA, NETWORK_ERROR, USERNAME_TAKEN
        assert "CAPTCHA" in captured
        assert "NETWORK_ERROR" in captured
        assert "USERNAME_TAKEN" in captured
        # Alasan ke-4 (TIMEOUT) tidak boleh muncul sebagai alasan gagal
        # (bisa muncul di bagian lain, tapi tidak di daftar top-3)
        lines = captured.splitlines()
        top3_lines = [l for l in lines if l.strip().startswith(("1.", "2.", "3."))]
        assert len(top3_lines) == 3

    def test_summary_shows_counts_for_each_reason(self, tmp_path, capsys):
        """summary() harus menampilkan jumlah kemunculan setiap alasan gagal."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        reasons = Counter({"CAPTCHA": 10, "NETWORK_ERROR": 7, "USERNAME_TAKEN": 5})
        stats = _make_stats(failure_reasons=reasons)

        logger.summary(stats)

        captured = capsys.readouterr().out
        assert "10" in captured
        assert "7" in captured
        assert "5" in captured

    def test_summary_shows_correct_rank_order(self, tmp_path, capsys):
        """Alasan gagal harus ditampilkan dari yang terbanyak ke yang paling sedikit."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        # Gunakan nama unik yang tidak muncul di teks summary lainnya
        reasons = Counter({"REASON_ALPHA": 3, "REASON_BRAVO": 10, "REASON_CHARLIE": 7})
        stats = _make_stats(failure_reasons=reasons)

        logger.summary(stats)

        captured = capsys.readouterr().out
        pos_bravo = captured.find("REASON_BRAVO")
        pos_charlie = captured.find("REASON_CHARLIE")
        pos_alpha = captured.find("REASON_ALPHA")
        # BRAVO (10) harus muncul sebelum CHARLIE (7), CHARLIE sebelum ALPHA (3)
        assert pos_bravo < pos_charlie < pos_alpha, (
            f"Urutan tidak benar: BRAVO@{pos_bravo}, CHARLIE@{pos_charlie}, ALPHA@{pos_alpha}"
        )

    def test_summary_no_failure_reasons_shows_no_failures_message(self, tmp_path, capsys):
        """Jika tidak ada kegagalan, summary() harus menampilkan pesan yang sesuai."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        stats = _make_stats(failed=0, failure_reasons=Counter())

        logger.summary(stats)

        captured = capsys.readouterr().out
        # Harus ada indikasi bahwa tidak ada kegagalan
        assert "tidak ada" in captured.lower() or "0" in captured

    def test_summary_with_exactly_three_reasons(self, tmp_path, capsys):
        """summary() dengan tepat 3 alasan gagal harus menampilkan ketiganya."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        reasons = Counter({"X": 5, "Y": 3, "Z": 1})
        stats = _make_stats(failure_reasons=reasons)

        logger.summary(stats)

        captured = capsys.readouterr().out
        assert "X" in captured
        assert "Y" in captured
        assert "Z" in captured

    def test_summary_with_fewer_than_three_reasons(self, tmp_path, capsys):
        """summary() dengan kurang dari 3 alasan gagal harus menampilkan semua yang ada."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        reasons = Counter({"ONLY_ONE": 4})
        stats = _make_stats(failure_reasons=reasons)

        logger.summary(stats)

        captured = capsys.readouterr().out
        assert "ONLY_ONE" in captured

    def test_summary_shows_total_sessions(self, tmp_path, capsys):
        """summary() harus menampilkan total sesi yang dijalankan."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        stats = _make_stats(total=42, successful=30, failed=12)

        logger.summary(stats)

        captured = capsys.readouterr().out
        assert "42" in captured

    def test_summary_shows_successful_count(self, tmp_path, capsys):
        """summary() harus menampilkan jumlah sesi berhasil."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        stats = _make_stats(total=10, successful=8, failed=2)

        logger.summary(stats)

        captured = capsys.readouterr().out
        assert "8" in captured

    def test_summary_shows_failed_count(self, tmp_path, capsys):
        """summary() harus menampilkan jumlah sesi gagal."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        stats = _make_stats(total=10, successful=8, failed=2)

        logger.summary(stats)

        captured = capsys.readouterr().out
        assert "2" in captured

    def test_summary_also_writes_to_log_file(self, tmp_path, capsys):
        """summary() harus juga mencatat ringkasan ke file log."""
        log_file = tmp_path / "bot_activity.log"
        logger = BotLogger(log_path=str(log_file))

        stats = _make_stats(total=5, successful=4, failed=1)

        logger.summary(stats)

        log_content = log_file.read_text(encoding="utf-8")
        # File log harus mengandung setidaknya satu entri dari summary
        assert len(log_content.strip()) > 0

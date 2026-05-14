"""
Unit tests untuk CredentialStore.

Mencakup:
- Format baris tersimpan: email|password|YYYY-MM-DD HH:MM:SS  (Req 8.1)
- Mode append — data lama tidak tertimpa                       (Req 8.2)
- Fallback ke console jika penulisan file gagal                (Req 8.5)
"""

from __future__ import annotations

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Tambahkan root proyek ke sys.path agar import credential_store berhasil
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))

from credential_store import CredentialStore


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

FIXED_DT = datetime(2024, 6, 15, 10, 30, 45)
FIXED_TS = "2024-06-15 10:30:45"


# ---------------------------------------------------------------------------
# Test 1 — Format baris: email|password|YYYY-MM-DD HH:MM:SS  (Req 8.1)
# ---------------------------------------------------------------------------


class TestSaveFormat:
    """Baris yang ditulis ke file harus mengikuti format yang ditentukan."""

    def test_line_format_email_password_timestamp(self, tmp_path):
        """Baris tersimpan dalam format `email|password|YYYY-MM-DD HH:MM:SS`."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        store.save("user@gmail.com", "P@ssw0rd123!", FIXED_DT)

        content = store_file.read_text(encoding="utf-8")
        assert content.strip() == f"user@gmail.com|P@ssw0rd123!|{FIXED_TS}"

    def test_line_ends_with_newline(self, tmp_path):
        """Setiap baris diakhiri newline agar entri berikutnya berada di baris baru."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        store.save("a@gmail.com", "Secret1!", FIXED_DT)

        content = store_file.read_text(encoding="utf-8")
        assert content.endswith("\n")

    def test_timestamp_format_yyyy_mm_dd_hh_mm_ss(self, tmp_path):
        """Timestamp harus menggunakan format YYYY-MM-DD HH:MM:SS."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        dt = datetime(2025, 1, 5, 8, 3, 7)
        store.save("test@gmail.com", "Abc123!@#", dt)

        content = store_file.read_text(encoding="utf-8")
        # Timestamp harus zero-padded
        assert "2025-01-05 08:03:07" in content

    def test_pipe_separator_used(self, tmp_path):
        """Pemisah antar field harus karakter `|`."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        store.save("sep@gmail.com", "MyPass1!", FIXED_DT)

        line = store_file.read_text(encoding="utf-8").strip()
        parts = line.split("|")
        assert len(parts) == 3, f"Diharapkan 3 bagian, dapat: {parts}"
        assert parts[0] == "sep@gmail.com"
        assert parts[1] == "MyPass1!"
        assert parts[2] == FIXED_TS


# ---------------------------------------------------------------------------
# Test 2 — Mode append: data lama tidak tertimpa  (Req 8.2)
# ---------------------------------------------------------------------------


class TestAppendMode:
    """Setiap panggilan `save` harus menambahkan baris baru tanpa menimpa data lama."""

    def test_second_save_does_not_overwrite_first(self, tmp_path):
        """Entri pertama tetap ada setelah entri kedua disimpan."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        dt1 = datetime(2024, 1, 1, 0, 0, 0)
        dt2 = datetime(2024, 1, 2, 0, 0, 0)

        store.save("first@gmail.com", "Pass1!", dt1)
        store.save("second@gmail.com", "Pass2!", dt2)

        content = store_file.read_text(encoding="utf-8")
        assert "first@gmail.com" in content
        assert "second@gmail.com" in content

    def test_multiple_saves_produce_multiple_lines(self, tmp_path):
        """Tiga panggilan `save` menghasilkan tepat tiga baris."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        for i in range(3):
            store.save(f"user{i}@gmail.com", f"Pass{i}!", FIXED_DT)

        lines = store_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3

    def test_existing_file_content_preserved(self, tmp_path):
        """Konten yang sudah ada di file sebelum `save` tidak dihapus."""
        store_file = tmp_path / "hasil_akun.txt"
        # Tulis konten awal secara manual
        store_file.write_text("existing@gmail.com|OldPass!|2023-12-31 23:59:59\n", encoding="utf-8")

        store = CredentialStore(storage_path=str(store_file))
        store.save("new@gmail.com", "NewPass!", FIXED_DT)

        content = store_file.read_text(encoding="utf-8")
        assert "existing@gmail.com" in content
        assert "new@gmail.com" in content

    def test_order_of_entries_preserved(self, tmp_path):
        """Urutan entri harus sesuai urutan pemanggilan `save`."""
        store_file = tmp_path / "hasil_akun.txt"
        store = CredentialStore(storage_path=str(store_file))

        emails = ["alpha@gmail.com", "beta@gmail.com", "gamma@gmail.com"]
        for email in emails:
            store.save(email, "Pass!", FIXED_DT)

        lines = store_file.read_text(encoding="utf-8").strip().splitlines()
        for i, email in enumerate(emails):
            assert lines[i].startswith(email)


# ---------------------------------------------------------------------------
# Test 3 — Fallback ke console jika penulisan file gagal  (Req 8.5)
# ---------------------------------------------------------------------------


class TestFallbackOnWriteError:
    """Jika `open` melempar PermissionError, kredensial harus tampil di console."""

    def test_fallback_prints_to_stdout_on_permission_error(self, capsys):
        """Kredensial dicetak ke stdout saat PermissionError terjadi."""
        store = CredentialStore(storage_path="/nonexistent/path/hasil_akun.txt")

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            store.save("fallback@gmail.com", "FallPass1!", FIXED_DT)

        captured = capsys.readouterr()
        assert "fallback@gmail.com" in captured.out
        assert "FallPass1!" in captured.out
        assert FIXED_TS in captured.out

    def test_fallback_output_contains_credential_line(self, capsys):
        """Output fallback harus mengandung baris kredensial lengkap."""
        store = CredentialStore(storage_path="/nonexistent/path/hasil_akun.txt")

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            store.save("full@gmail.com", "FullPass1!", FIXED_DT)

        captured = capsys.readouterr()
        expected_line = f"full@gmail.com|FullPass1!|{FIXED_TS}"
        assert expected_line in captured.out

    def test_fallback_logs_error_to_logger_when_provided(self, capsys):
        """Jika logger disediakan, error harus dicatat ke logger dengan level ERROR."""
        mock_logger = MagicMock()
        store = CredentialStore(
            storage_path="/nonexistent/path/hasil_akun.txt",
            logger=mock_logger,
        )

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            store.save("logged@gmail.com", "LogPass1!", FIXED_DT)

        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        # Argumen pertama adalah component, argumen kedua adalah pesan error
        error_message = call_args[0][1]
        assert "logged@gmail.com" in error_message

    def test_fallback_does_not_raise_exception(self, capsys):
        """Kegagalan penulisan tidak boleh melempar exception ke pemanggil."""
        store = CredentialStore(storage_path="/nonexistent/path/hasil_akun.txt")

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            # Tidak boleh raise
            store.save("safe@gmail.com", "SafePass1!", FIXED_DT)

    def test_fallback_without_logger_does_not_raise(self, capsys):
        """Fallback tanpa logger (logger=None) tidak boleh melempar AttributeError."""
        store = CredentialStore(
            storage_path="/nonexistent/path/hasil_akun.txt",
            logger=None,
        )

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            store.save("nolog@gmail.com", "NoLogPass1!", FIXED_DT)

        captured = capsys.readouterr()
        assert "nolog@gmail.com" in captured.out

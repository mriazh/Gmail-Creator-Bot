"""
Unit tests untuk ConfigLoader.

Mencakup:
- File tidak ditemukan → buat default dan exit (Req 11.3)
- JSON tidak valid → tampilkan lokasi error dan exit (Req 11.4)
- Field valid → list kosong dikembalikan (Req 11.5)
- Beberapa field invalid → semua field invalid dilaporkan (Req 11.5)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Tambahkan project root ke sys.path agar import config_loader dan models bisa berjalan
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config_loader import ConfigLoader, ConfigError, DEFAULT_CONFIG
from models import BotConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_CONFIG: dict = {
    "seed_accounts": [],
    "phone_numbers": [],
    "accounts_per_ip_rotation": 5,
    "delay_min": 30,
    "delay_max": 90,
    "total_accounts": 10,
    "faker_locale": "en_US",
}


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# Test: file tidak ditemukan → buat default dan exit (Req 11.3)
# ---------------------------------------------------------------------------

class TestFileNotFound:
    """Ketika config.json tidak ada, ConfigLoader harus membuat file default lalu exit."""

    def test_creates_default_file_when_missing(self, tmp_path: Path) -> None:
        """File default harus dibuat di path yang diberikan."""
        config_path = tmp_path / "config.json"
        loader = ConfigLoader()

        with pytest.raises(SystemExit):
            loader.load(str(config_path))

        assert config_path.exists(), "File default harus dibuat"

    def test_default_file_contains_valid_json(self, tmp_path: Path) -> None:
        """File default yang dibuat harus berisi JSON yang valid."""
        config_path = tmp_path / "config.json"
        loader = ConfigLoader()

        with pytest.raises(SystemExit):
            loader.load(str(config_path))

        content = json.loads(config_path.read_text(encoding="utf-8"))
        assert isinstance(content, dict)

    def test_default_file_has_all_required_keys(self, tmp_path: Path) -> None:
        """File default harus memiliki semua key yang diperlukan sesuai DEFAULT_CONFIG."""
        config_path = tmp_path / "config.json"
        loader = ConfigLoader()

        with pytest.raises(SystemExit):
            loader.load(str(config_path))

        content = json.loads(config_path.read_text(encoding="utf-8"))
        for key in DEFAULT_CONFIG:
            assert key in content, f"Key '{key}' harus ada di file default"

    def test_exits_with_code_zero(self, tmp_path: Path) -> None:
        """Exit code harus 0 (instruksi ke pengguna, bukan error)."""
        config_path = tmp_path / "config.json"
        loader = ConfigLoader()

        with pytest.raises(SystemExit) as exc_info:
            loader.load(str(config_path))

        assert exc_info.value.code == 0

    def test_prints_instruction_message(self, tmp_path: Path, capsys) -> None:
        """Harus mencetak pesan instruksi ke console."""
        config_path = tmp_path / "config.json"
        loader = ConfigLoader()

        with pytest.raises(SystemExit):
            loader.load(str(config_path))

        captured = capsys.readouterr()
        assert "tidak ditemukan" in captured.out or "default" in captured.out.lower()

    def test_creates_parent_directories_if_needed(self, tmp_path: Path) -> None:
        """Harus membuat direktori parent jika belum ada."""
        config_path = tmp_path / "subdir" / "nested" / "config.json"
        loader = ConfigLoader()

        with pytest.raises(SystemExit):
            loader.load(str(config_path))

        assert config_path.exists()


# ---------------------------------------------------------------------------
# Test: JSON tidak valid → tampilkan lokasi error dan exit (Req 11.4)
# ---------------------------------------------------------------------------

class TestInvalidJson:
    """Ketika config.json berisi JSON tidak valid, harus raise ConfigError dengan lokasi error."""

    def test_raises_config_error_on_invalid_json(self, tmp_path: Path) -> None:
        """Harus raise ConfigError jika JSON tidak valid."""
        config_path = tmp_path / "config.json"
        config_path.write_text("{invalid json: true,}", encoding="utf-8")
        loader = ConfigLoader()

        with pytest.raises(ConfigError):
            loader.load(str(config_path))

    def test_error_message_contains_line_number(self, tmp_path: Path) -> None:
        """Pesan error harus menyebutkan nomor baris lokasi kesalahan."""
        config_path = tmp_path / "config.json"
        config_path.write_text('{\n  "key": invalid\n}', encoding="utf-8")
        loader = ConfigLoader()

        with pytest.raises(ConfigError) as exc_info:
            loader.load(str(config_path))

        assert "baris" in str(exc_info.value).lower() or "line" in str(exc_info.value).lower()

    def test_error_message_contains_column_number(self, tmp_path: Path) -> None:
        """Pesan error harus menyebutkan nomor kolom lokasi kesalahan."""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"key": invalid}', encoding="utf-8")
        loader = ConfigLoader()

        with pytest.raises(ConfigError) as exc_info:
            loader.load(str(config_path))

        assert "kolom" in str(exc_info.value).lower() or "col" in str(exc_info.value).lower()

    def test_error_message_contains_file_path(self, tmp_path: Path) -> None:
        """Pesan error harus menyebutkan path file yang bermasalah."""
        config_path = tmp_path / "config.json"
        config_path.write_text("{bad}", encoding="utf-8")
        loader = ConfigLoader()

        with pytest.raises(ConfigError) as exc_info:
            loader.load(str(config_path))

        assert str(config_path) in str(exc_info.value) or "config.json" in str(exc_info.value)

    def test_empty_file_raises_config_error(self, tmp_path: Path) -> None:
        """File kosong juga harus raise ConfigError."""
        config_path = tmp_path / "config.json"
        config_path.write_text("", encoding="utf-8")
        loader = ConfigLoader()

        with pytest.raises(ConfigError):
            loader.load(str(config_path))

    def test_truncated_json_raises_config_error(self, tmp_path: Path) -> None:
        """JSON yang terpotong harus raise ConfigError."""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"seed_accounts": [', encoding="utf-8")
        loader = ConfigLoader()

        with pytest.raises(ConfigError):
            loader.load(str(config_path))


# ---------------------------------------------------------------------------
# Test: field valid → list kosong dikembalikan (Req 11.5)
# ---------------------------------------------------------------------------

class TestValidConfig:
    """Ketika semua field valid, validate() harus mengembalikan list kosong."""

    def test_validate_returns_empty_list_for_valid_config(self) -> None:
        """validate() harus mengembalikan [] jika semua field valid."""
        loader = ConfigLoader()
        result = loader.validate(VALID_CONFIG)
        assert result == []

    def test_load_returns_bot_config_for_valid_file(self, tmp_path: Path) -> None:
        """load() harus mengembalikan BotConfig jika file valid."""
        config_path = tmp_path / "config.json"
        write_json(config_path, VALID_CONFIG)
        loader = ConfigLoader()

        result = loader.load(str(config_path))

        assert isinstance(result, BotConfig)

    def test_load_maps_fields_correctly(self, tmp_path: Path) -> None:
        """BotConfig yang dikembalikan harus memiliki nilai yang sesuai dengan config."""
        config_path = tmp_path / "config.json"
        write_json(config_path, VALID_CONFIG)
        loader = ConfigLoader()

        result = loader.load(str(config_path))

        assert result.accounts_per_ip_rotation == VALID_CONFIG["accounts_per_ip_rotation"]
        assert result.delay_min == VALID_CONFIG["delay_min"]
        assert result.delay_max == VALID_CONFIG["delay_max"]
        assert result.total_accounts == VALID_CONFIG["total_accounts"]
        assert result.faker_locale == VALID_CONFIG["faker_locale"]

    def test_validate_accepts_boundary_values(self) -> None:
        """validate() harus menerima nilai di batas rentang yang valid."""
        boundary_config = {
            "seed_accounts": [],
            "phone_numbers": [],
            "accounts_per_ip_rotation": 1,   # batas bawah
            "delay_min": 1,                   # batas bawah
            "delay_max": 3600,                # batas atas
            "total_accounts": 10000,          # batas atas
        }
        loader = ConfigLoader()
        result = loader.validate(boundary_config)
        assert result == []

    def test_validate_accepts_max_boundary_accounts_per_ip(self) -> None:
        """accounts_per_ip_rotation = 50 harus valid."""
        config = {**VALID_CONFIG, "accounts_per_ip_rotation": 50}
        loader = ConfigLoader()
        assert loader.validate(config) == []

    def test_validate_accepts_seed_accounts_with_entries(self, tmp_path: Path) -> None:
        """seed_accounts dengan entri valid harus diterima."""
        config = {
            **VALID_CONFIG,
            "seed_accounts": [
                {"email": "seed@gmail.com", "password": "pass123"},
            ],
        }
        config_path = tmp_path / "config.json"
        write_json(config_path, config)
        loader = ConfigLoader()

        result = loader.load(str(config_path))

        assert len(result.seed_accounts) == 1
        assert result.seed_accounts[0].email == "seed@gmail.com"

    def test_validate_faker_locale_optional(self) -> None:
        """faker_locale bersifat opsional; config tanpa field ini harus valid."""
        config = {k: v for k, v in VALID_CONFIG.items() if k != "faker_locale"}
        loader = ConfigLoader()
        assert loader.validate(config) == []


# ---------------------------------------------------------------------------
# Test: beberapa field invalid → semua field invalid dilaporkan (Req 11.5)
# ---------------------------------------------------------------------------

class TestInvalidFields:
    """validate() harus melaporkan semua field yang tidak valid sekaligus."""

    def test_missing_required_field_reported(self) -> None:
        """Field wajib yang hilang harus dilaporkan."""
        config = {k: v for k, v in VALID_CONFIG.items() if k != "seed_accounts"}
        loader = ConfigLoader()
        result = loader.validate(config)
        assert "seed_accounts" in result

    def test_multiple_missing_fields_all_reported(self) -> None:
        """Semua field wajib yang hilang harus dilaporkan sekaligus."""
        loader = ConfigLoader()
        result = loader.validate({})
        expected_fields = {
            "seed_accounts", "phone_numbers", "accounts_per_ip_rotation",
            "delay_min", "delay_max", "total_accounts",
        }
        for field in expected_fields:
            assert field in result, f"Field '{field}' harus dilaporkan sebagai tidak valid"

    def test_out_of_range_accounts_per_ip_rotation_reported(self) -> None:
        """accounts_per_ip_rotation di luar rentang 1–50 harus dilaporkan."""
        loader = ConfigLoader()

        result_zero = loader.validate({**VALID_CONFIG, "accounts_per_ip_rotation": 0})
        assert "accounts_per_ip_rotation" in result_zero

        result_over = loader.validate({**VALID_CONFIG, "accounts_per_ip_rotation": 51})
        assert "accounts_per_ip_rotation" in result_over

    def test_out_of_range_delay_min_reported(self) -> None:
        """delay_min di luar rentang 1–3600 harus dilaporkan."""
        loader = ConfigLoader()

        result_zero = loader.validate({**VALID_CONFIG, "delay_min": 0})
        assert "delay_min" in result_zero

        result_over = loader.validate({**VALID_CONFIG, "delay_min": 3601})
        assert "delay_min" in result_over

    def test_out_of_range_delay_max_reported(self) -> None:
        """delay_max di luar rentang 1–3600 harus dilaporkan."""
        loader = ConfigLoader()

        result_zero = loader.validate({**VALID_CONFIG, "delay_max": 0})
        assert "delay_max" in result_zero

        result_over = loader.validate({**VALID_CONFIG, "delay_max": 3601})
        assert "delay_max" in result_over

    def test_delay_max_less_than_delay_min_reported(self) -> None:
        """delay_max < delay_min harus dilaporkan sebagai tidak valid."""
        config = {**VALID_CONFIG, "delay_min": 60, "delay_max": 30}
        loader = ConfigLoader()
        result = loader.validate(config)
        assert "delay_max" in result

    def test_out_of_range_total_accounts_reported(self) -> None:
        """total_accounts di luar rentang 1–10000 harus dilaporkan."""
        loader = ConfigLoader()

        result_zero = loader.validate({**VALID_CONFIG, "total_accounts": 0})
        assert "total_accounts" in result_zero

        result_over = loader.validate({**VALID_CONFIG, "total_accounts": 10001})
        assert "total_accounts" in result_over

    def test_wrong_type_for_integer_field_reported(self) -> None:
        """Tipe data yang salah (string bukan int) harus dilaporkan."""
        loader = ConfigLoader()

        result = loader.validate({**VALID_CONFIG, "accounts_per_ip_rotation": "5"})
        assert "accounts_per_ip_rotation" in result

    def test_boolean_not_accepted_as_integer(self) -> None:
        """Boolean tidak boleh diterima sebagai integer (bool adalah subclass int di Python)."""
        loader = ConfigLoader()

        result = loader.validate({**VALID_CONFIG, "accounts_per_ip_rotation": True})
        assert "accounts_per_ip_rotation" in result

    def test_seed_accounts_exceeding_max_reported(self) -> None:
        """seed_accounts dengan lebih dari 100 entri harus dilaporkan."""
        too_many = [{"email": f"a{i}@g.com", "password": "p"} for i in range(101)]
        loader = ConfigLoader()
        result = loader.validate({**VALID_CONFIG, "seed_accounts": too_many})
        assert "seed_accounts" in result

    def test_phone_numbers_exceeding_max_reported(self) -> None:
        """phone_numbers dengan lebih dari 100 entri harus dilaporkan."""
        too_many = [f"+628{i:09d}" for i in range(101)]
        loader = ConfigLoader()
        result = loader.validate({**VALID_CONFIG, "phone_numbers": too_many})
        assert "phone_numbers" in result

    def test_faker_locale_wrong_type_reported(self) -> None:
        """faker_locale dengan tipe bukan string harus dilaporkan."""
        loader = ConfigLoader()
        result = loader.validate({**VALID_CONFIG, "faker_locale": 123})
        assert "faker_locale" in result

    def test_multiple_invalid_fields_all_reported_simultaneously(self) -> None:
        """Semua field yang tidak valid harus dilaporkan dalam satu panggilan validate()."""
        bad_config = {
            "seed_accounts": "bukan_list",
            "phone_numbers": "bukan_list",
            "accounts_per_ip_rotation": 0,
            "delay_min": -1,
            "delay_max": 9999,
            "total_accounts": 0,
        }
        loader = ConfigLoader()
        result = loader.validate(bad_config)

        assert "seed_accounts" in result
        assert "phone_numbers" in result
        assert "accounts_per_ip_rotation" in result
        assert "delay_min" in result
        assert "total_accounts" in result

    def test_load_raises_config_error_with_invalid_fields_listed(self, tmp_path: Path) -> None:
        """load() harus raise ConfigError yang menyebutkan field-field yang tidak valid."""
        bad_config = {
            **VALID_CONFIG,
            "accounts_per_ip_rotation": 0,
            "total_accounts": 0,
        }
        config_path = tmp_path / "config.json"
        write_json(config_path, bad_config)
        loader = ConfigLoader()

        with pytest.raises(ConfigError) as exc_info:
            loader.load(str(config_path))

        error_msg = str(exc_info.value)
        assert "accounts_per_ip_rotation" in error_msg
        assert "total_accounts" in error_msg

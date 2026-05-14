"""
ConfigLoader untuk Gmail Creator Bot.

Memuat dan memvalidasi config.json saat startup.
- Jika file tidak ditemukan: buat file default dan exit.
- Jika JSON tidak valid: tampilkan lokasi error dan exit.
- Jika field tidak valid: kembalikan daftar field yang tidak valid.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from models import BotConfig, SeedAccount


# Skema default config sesuai design document
DEFAULT_CONFIG: dict[str, Any] = {
    "seed_accounts": [],
    "phone_numbers": [],
    "accounts_per_ip_rotation": 5,
    "delay_min": 30,
    "delay_max": 90,
    "total_accounts": 10,
    "faker_locale": "en_US",
}


class ConfigError(Exception):
    """Exception yang di-raise saat konfigurasi tidak valid."""
    pass


class ConfigLoader:
    """Memuat dan memvalidasi konfigurasi bot dari config.json."""

    def load(self, path: str) -> BotConfig:
        """Muat config.json, buat default jika tidak ada, raise ConfigError jika invalid.

        Args:
            path: Path ke file config.json.

        Returns:
            BotConfig yang sudah divalidasi.

        Raises:
            ConfigError: Jika JSON tidak valid atau field tidak valid.
            SystemExit: Jika file tidak ditemukan (setelah membuat default).
        """
        config_path = Path(path)

        # Jika file tidak ditemukan: buat default dan exit
        if not config_path.exists():
            self._create_default_config(config_path)
            print(
                f"[ConfigLoader] File '{path}' tidak ditemukan.\n"
                f"File konfigurasi default telah dibuat di '{config_path.resolve()}'.\n"
                f"Silakan isi konfigurasi sesuai kebutuhan, lalu jalankan bot kembali."
            )
            sys.exit(0)

        # Baca dan parse JSON
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"File '{path}' mengandung format JSON yang tidak valid. "
                f"Lokasi kesalahan: baris {e.lineno}, kolom {e.colno}. "
                f"Detail: {e.msg}"
            ) from e

        # Validasi field
        invalid_fields = self.validate(raw)
        if invalid_fields:
            raise ConfigError(
                f"Field konfigurasi tidak valid: {', '.join(invalid_fields)}"
            )

        # Bangun BotConfig dari dict
        return self._build_config(raw)

    def validate(self, config: dict) -> list[str]:
        """Periksa semua field wajib dan rentang nilai.

        Args:
            config: Dictionary konfigurasi yang akan divalidasi.

        Returns:
            Daftar nama field yang tidak valid. List kosong berarti semua valid.
        """
        invalid: list[str] = []

        # seed_accounts: required, list, max 100 entries
        if "seed_accounts" not in config:
            invalid.append("seed_accounts")
        else:
            val = config["seed_accounts"]
            if not isinstance(val, list) or len(val) > 100:
                invalid.append("seed_accounts")

        # phone_numbers: required, list, max 100 entries
        if "phone_numbers" not in config:
            invalid.append("phone_numbers")
        else:
            val = config["phone_numbers"]
            if not isinstance(val, list) or len(val) > 100:
                invalid.append("phone_numbers")

        # accounts_per_ip_rotation: required, int, range 1–50
        if "accounts_per_ip_rotation" not in config:
            invalid.append("accounts_per_ip_rotation")
        else:
            val = config["accounts_per_ip_rotation"]
            if not isinstance(val, int) or isinstance(val, bool) or not (1 <= val <= 50):
                invalid.append("accounts_per_ip_rotation")

        # delay_min: required, int, range 1–3600
        delay_min_ok = True
        if "delay_min" not in config:
            invalid.append("delay_min")
            delay_min_ok = False
        else:
            val = config["delay_min"]
            if not isinstance(val, int) or isinstance(val, bool) or not (1 <= val <= 3600):
                invalid.append("delay_min")
                delay_min_ok = False

        # delay_max: required, int, range 1–3600, >= delay_min
        if "delay_max" not in config:
            invalid.append("delay_max")
        else:
            val = config["delay_max"]
            if not isinstance(val, int) or isinstance(val, bool) or not (1 <= val <= 3600):
                invalid.append("delay_max")
            elif delay_min_ok and val < config["delay_min"]:
                invalid.append("delay_max")

        # total_accounts: required, int, range 1–10000
        if "total_accounts" not in config:
            invalid.append("total_accounts")
        else:
            val = config["total_accounts"]
            if not isinstance(val, int) or isinstance(val, bool) or not (1 <= val <= 10000):
                invalid.append("total_accounts")

        # faker_locale: optional string, default "en_US"
        if "faker_locale" in config:
            val = config["faker_locale"]
            if not isinstance(val, str):
                invalid.append("faker_locale")

        return invalid

    def _create_default_config(self, path: Path) -> None:
        """Buat file config.json dengan nilai default.

        Args:
            path: Path ke file yang akan dibuat.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)

    def _build_config(self, raw: dict) -> BotConfig:
        """Bangun objek BotConfig dari dictionary yang sudah divalidasi.

        Args:
            raw: Dictionary konfigurasi yang sudah divalidasi.

        Returns:
            Objek BotConfig.
        """
        seed_accounts: list[SeedAccount] = []
        for entry in raw.get("seed_accounts", []):
            if isinstance(entry, dict) and "email" in entry and "password" in entry:
                seed_accounts.append(
                    SeedAccount(email=str(entry["email"]), password=str(entry["password"]))
                )

        return BotConfig(
            seed_accounts=seed_accounts,
            phone_numbers=[str(p) for p in raw.get("phone_numbers", [])],
            accounts_per_ip_rotation=int(raw["accounts_per_ip_rotation"]),
            delay_min=int(raw["delay_min"]),
            delay_max=int(raw["delay_max"]),
            total_accounts=int(raw["total_accounts"]),
            faker_locale=str(raw.get("faker_locale", "en_US")),
        )

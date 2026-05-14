"""
PhoneTracker — Melacak penggunaan nomor HP untuk verifikasi SMS.

Komponen ini bertanggung jawab untuk:
- Membaca dan menyimpan data penggunaan nomor HP ke phone_usage.json
- Menampilkan daftar nomor HP beserta jumlah penggunaan saat prompt input
- Memvalidasi format nomor HP (digit + opsional '+' di awal, panjang 8–15 karakter)
- Menangani timeout 120 detik saat menunggu input pengguna
"""

from __future__ import annotations

import json
import re
import sys
import threading
from pathlib import Path
from typing import Optional


# Pola validasi: opsional '+' di awal, diikuti hanya digit, total panjang 8–15 karakter
_PHONE_PATTERN = re.compile(r"^\+?\d{8,15}$")


def validate_phone_format(phone_number: str) -> bool:
    """Validasi format nomor HP.

    Aturan:
    - Hanya digit, boleh diawali tanda '+'
    - Panjang total 8–15 karakter (termasuk '+' jika ada)

    Args:
        phone_number: String nomor HP yang akan divalidasi.

    Returns:
        True jika format valid, False jika tidak.
    """
    return bool(_PHONE_PATTERN.match(phone_number))


class PhoneTracker:
    """Melacak penggunaan nomor HP untuk verifikasi SMS OTP.

    Attributes:
        storage_path: Path ke file JSON penyimpanan data penggunaan.
    """

    def __init__(self, storage_path: str = "phone_usage.json") -> None:
        """Inisialisasi PhoneTracker.

        Args:
            storage_path: Path ke file phone_usage.json.
                          Default: "phone_usage.json" di direktori kerja saat ini.
        """
        self.storage_path = Path(storage_path)

    def get_usage(self) -> dict[str, int]:
        """Baca data penggunaan nomor HP dari phone_usage.json.

        Jika file tidak ditemukan atau kosong, kembalikan dict kosong.

        Returns:
            Dict dengan format {nomor_hp: jumlah_penggunaan}.
        """
        if not self.storage_path.exists():
            return {}

        try:
            content = self.storage_path.read_text(encoding="utf-8").strip()
            if not content:
                return {}
            data = json.loads(content)
            # Pastikan semua nilai adalah integer
            return {k: int(v) for k, v in data.items()}
        except (json.JSONDecodeError, ValueError, OSError):
            return {}

    def record_usage(self, phone_number: str) -> None:
        """Tambah hitungan penggunaan nomor HP sebesar 1 dan simpan ke phone_usage.json.

        Jika nomor belum ada di file, hitungan dimulai dari 1.
        Data disimpan secara persisten sehingga tetap ada antar sesi.

        Args:
            phone_number: Nomor HP yang digunakan untuk verifikasi.
        """
        usage = self.get_usage()
        usage[phone_number] = usage.get(phone_number, 0) + 1

        self.storage_path.write_text(
            json.dumps(usage, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def prompt_phone_input(
        self,
        available_numbers: list[str],
        timeout: int = 120,
    ) -> Optional[str]:
        """Tampilkan daftar nomor HP + usage, minta input manual, validasi format.

        Menampilkan tabel nomor HP yang tersedia beserta jumlah penggunaan masing-masing,
        lalu menunggu pengguna memasukkan nomor HP. Input divalidasi formatnya sebelum
        diterima. Jika pengguna tidak memasukkan nomor dalam batas waktu, kembalikan None.

        Args:
            available_numbers: Daftar nomor HP yang tersedia dari config.json.
            timeout: Batas waktu tunggu input dalam detik (default: 120).

        Returns:
            Nomor HP yang valid yang dimasukkan pengguna, atau None jika timeout.
        """
        usage = self.get_usage()

        # Tampilkan daftar nomor HP beserta jumlah penggunaan
        print("\n" + "=" * 50)
        print("VERIFIKASI NOMOR HP DIPERLUKAN")
        print("=" * 50)
        print("Daftar nomor HP yang tersedia:")
        print(f"  {'No.':<5} {'Nomor HP':<20} {'Penggunaan':>10}")
        print(f"  {'-'*5} {'-'*20} {'-'*10}")
        for idx, number in enumerate(available_numbers, start=1):
            count = usage.get(number, 0)
            print(f"  {idx:<5} {number:<20} {count:>10}x")
        print("=" * 50)
        print(f"Masukkan nomor HP (timeout: {timeout} detik):")
        print("Format: hanya digit, boleh diawali '+', panjang 8–15 karakter")
        print("Contoh: +628123456789 atau 08123456789")

        result: list[Optional[str]] = [None]
        timed_out = threading.Event()

        def _read_input() -> None:
            """Baca input dari stdin dalam thread terpisah."""
            while not timed_out.is_set():
                try:
                    raw = input("> ").strip()
                except EOFError:
                    break

                if timed_out.is_set():
                    break

                if not validate_phone_format(raw):
                    print(
                        f"[ERROR] Format nomor HP tidak valid: '{raw}'\n"
                        "Format yang diterima: hanya digit, boleh diawali '+', "
                        "panjang 8–15 karakter.\n"
                        "Silakan masukkan ulang:"
                    )
                    continue

                result[0] = raw
                timed_out.set()
                break

        input_thread = threading.Thread(target=_read_input, daemon=True)
        input_thread.start()
        input_thread.join(timeout=timeout)

        if result[0] is None:
            # Timeout — set event agar thread berhenti jika masih berjalan
            timed_out.set()
            print(
                f"\n[WARNING] Timeout: tidak ada input nomor HP dalam {timeout} detik. "
                "Sesi ini akan dilewati."
            )
            return None

        return result[0]

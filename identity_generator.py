"""
IdentityGenerator — menghasilkan identitas palsu untuk pembuatan akun Gmail.

Menggunakan library Faker untuk nama, dan menghasilkan tanggal lahir,
username Gmail, serta password yang memenuhi semua aturan validasi.
"""

from __future__ import annotations

import logging
import random
import re
import secrets
import string
from datetime import date, timedelta
from typing import Optional

from faker import Faker

from models import Identity

logger = logging.getLogger(__name__)

# Aturan format username Gmail
_GMAIL_USERNAME_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9.]{4,28}[a-zA-Z0-9]$')
_CONSECUTIVE_DOTS_RE = re.compile(r'\.\.')


def _is_valid_gmail_username(username: str) -> bool:
    """Periksa apakah username memenuhi aturan format Gmail.

    Aturan:
    - Panjang 6–30 karakter
    - Hanya huruf, angka, dan titik
    - Tidak ada titik berurutan (..)
    - Tidak diawali atau diakhiri titik
    """
    if not username:
        return False
    if len(username) < 6 or len(username) > 30:
        return False
    # Hanya huruf, angka, titik
    if not re.match(r'^[a-zA-Z0-9.]+$', username):
        return False
    # Tidak diawali atau diakhiri titik
    if username.startswith('.') or username.endswith('.'):
        return False
    # Tidak ada titik berurutan
    if _CONSECUTIVE_DOTS_RE.search(username):
        return False
    return True


class IdentityGenerator:
    """Menghasilkan identitas palsu untuk pendaftaran akun Gmail.

    Attributes:
        locale: Locale Faker yang digunakan (default: "en_US").
    """

    _MAX_USERNAME_RETRIES = 5

    def __init__(self, locale: str = "en_US") -> None:
        self.locale = locale
        self._faker = Faker(locale)
        # Set untuk tracking username yang sudah dihasilkan dalam batch ini
        self._used_usernames: set[str] = set()

    def generate(self) -> Identity:
        """Hasilkan identitas lengkap: nama, tanggal lahir, username, password, email.

        Returns:
            Identity yang memenuhi semua kriteria validasi.

        Raises:
            RuntimeError: Jika username tidak dapat dihasilkan setelah 5 percobaan.
        """
        first_name = self._faker.first_name()
        last_name = self._faker.last_name()
        birth_date = self._generate_birth_date()
        username = self._generate_username(first_name, last_name)
        password = self._generate_password()
        email = f"{username}@gmail.com"

        # Tandai username sebagai sudah digunakan dalam batch ini
        self._used_usernames.add(username)

        return Identity(
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            username=username,
            password=password,
            email=email,
        )

    def _generate_birth_date(self) -> date:
        """Hasilkan tanggal lahir dengan usia antara 18 dan 40 tahun dari hari ini."""
        today = date.today()
        # Batas usia: 18–40 tahun
        min_age_days = 18 * 365
        max_age_days = 40 * 365
        days_offset = random.randint(min_age_days, max_age_days)
        return today - timedelta(days=days_offset)

    def _generate_username(self, first: str, last: str) -> str:
        """Hasilkan username Gmail dari kombinasi nama + angka acak.

        Mencoba hingga 5 kali untuk menghasilkan username yang:
        - Memenuhi format Gmail (6–30 karakter, hanya huruf/angka/titik)
        - Unik dalam batch eksekusi saat ini

        Args:
            first: Nama depan.
            last: Nama belakang.

        Returns:
            Username yang valid dan unik.

        Raises:
            RuntimeError: Jika tidak berhasil menghasilkan username valid setelah 5 percobaan.
        """
        # Bersihkan nama: hanya huruf dan angka, lowercase
        clean_first = re.sub(r'[^a-zA-Z0-9]', '', first).lower()
        clean_last = re.sub(r'[^a-zA-Z0-9]', '', last).lower()

        for attempt in range(1, self._MAX_USERNAME_RETRIES + 1):
            number = random.randint(1, 9999)

            # Beberapa strategi kombinasi nama
            candidates = [
                f"{clean_first}{clean_last}{number}",
                f"{clean_first}.{clean_last}{number}",
                f"{clean_first}{number}",
                f"{clean_last}{number}",
                f"{clean_first}.{number}",
            ]

            for candidate in candidates:
                if _is_valid_gmail_username(candidate) and candidate not in self._used_usernames:
                    return candidate

            logger.warning(
                "IdentityGenerator: percobaan %d/%d gagal menghasilkan username valid "
                "untuk nama '%s %s'",
                attempt,
                self._MAX_USERNAME_RETRIES,
                first,
                last,
            )

        # Semua percobaan habis
        error_msg = (
            f"Gagal menghasilkan username Gmail valid setelah "
            f"{self._MAX_USERNAME_RETRIES} percobaan untuk nama '{first} {last}'"
        )
        logger.error("IdentityGenerator: %s", error_msg)
        raise RuntimeError(error_msg)

    def _generate_password(self) -> str:
        """Hasilkan password yang memenuhi kriteria keamanan.

        Kriteria:
        - Panjang minimal 12 karakter
        - Mengandung minimal 1 huruf besar
        - Mengandung minimal 1 huruf kecil
        - Mengandung minimal 1 angka
        - Mengandung minimal 1 simbol

        Returns:
            Password yang memenuhi semua kriteria.
        """
        # Karakter yang diizinkan per kategori
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        symbols = string.punctuation

        # Pastikan minimal 1 karakter dari setiap kategori
        password_chars = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]

        # Isi sisa karakter (minimal 12 total, tambah 8 lagi = 12 total)
        all_chars = uppercase + lowercase + digits + symbols
        remaining_length = random.randint(8, 12)  # total 12–16 karakter
        password_chars.extend(secrets.choice(all_chars) for _ in range(remaining_length))

        # Acak urutan karakter
        random.shuffle(password_chars)
        return ''.join(password_chars)

    def reset_batch(self) -> None:
        """Reset tracking username untuk memulai batch baru.

        Panggil method ini di awal setiap batch eksekusi baru.
        """
        self._used_usernames.clear()

    @property
    def used_usernames(self) -> frozenset[str]:
        """Kembalikan set username yang sudah dihasilkan dalam batch ini (read-only)."""
        return frozenset(self._used_usernames)

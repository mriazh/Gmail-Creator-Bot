"""
Seed Account Rotator untuk Gmail Creator Bot.

Mengelola rotasi round-robin seed account dari daftar yang tersedia.
Mendukung penandaan akun sebagai gagal permanen (dikecualikan dari run ini)
atau gagal sementara (dilewati sesi ini, kembali di putaran berikutnya).
"""

from __future__ import annotations

import logging
from typing import Optional

from models import SeedAccount

logger = logging.getLogger(__name__)


class NoSeedAccountError(Exception):
    """Raised ketika semua seed account tidak tersedia (semua gagal atau dikecualikan).

    Sesuai Requirement 2.7: jika semua seed account dalam daftar tidak tersedia,
    bot harus menghentikan eksekusi dan mencatat kondisi kegagalan ke Logger
    dengan level ERROR.
    """


class SeedAccountRotator:
    """Mengelola rotasi round-robin seed account.

    Seed account dipilih secara berurutan sesuai urutan entri dalam konfigurasi.
    Setelah semua akun digunakan satu putaran, rotasi kembali ke akun pertama.

    Akun yang ditandai permanent-failed dikecualikan dari seluruh run saat ini.
    Akun yang ditandai temporary-failed dilewati untuk sesi ini saja dan akan
    kembali masuk rotasi pada putaran berikutnya.

    Entri tanpa field email atau password dilewati dengan log WARNING saat
    konstruksi.

    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8
    """

    def __init__(self, accounts: list[SeedAccount]) -> None:
        """Inisialisasi rotator dengan daftar seed account.

        Entri yang tidak memiliki email atau password (string kosong) akan
        dilewati dengan log WARNING sesuai Requirement 2.8.

        Args:
            accounts: Daftar seed account dari konfigurasi.
        """
        # Filter entri yang tidak valid (tanpa email atau password)
        valid_accounts: list[SeedAccount] = []
        for account in accounts:
            if not account.email or not account.password:
                logger.warning(
                    "Melewati entri seed account yang tidak memiliki field "
                    "email atau password: email=%r, password=%r",
                    account.email,
                    account.password,
                )
            else:
                valid_accounts.append(account)

        # Daftar akun yang valid dan aktif dalam rotasi
        self._accounts: list[SeedAccount] = valid_accounts

        # Set email akun yang dikecualikan secara permanen dari run ini
        self._permanent_failed: set[str] = set()

        # Set email akun yang dilewati sementara untuk putaran saat ini
        self._temporary_skipped: set[str] = set()

        # Indeks akun berikutnya dalam rotasi (mengacu ke self._accounts)
        self._current_index: int = 0

    def next(self) -> SeedAccount:
        """Kembalikan seed account berikutnya secara round-robin.

        Akun yang ditandai permanent-failed selalu dilewati.
        Akun yang ditandai temporary-failed dilewati untuk putaran saat ini;
        saat rotasi kembali ke awal (wrap-around), temporary-failed direset
        sehingga akun tersebut kembali tersedia.

        Returns:
            SeedAccount berikutnya yang tersedia.

        Raises:
            NoSeedAccountError: Jika semua seed account tidak tersedia
                (semua permanent-failed, atau semua tersisa temporary-skipped
                dan tidak ada yang bisa digunakan dalam putaran ini).
        """
        total = len(self._accounts)
        if total == 0:
            raise NoSeedAccountError(
                "Tidak ada seed account yang valid dalam daftar konfigurasi."
            )

        # Lacak berapa banyak akun yang sudah dicoba dalam putaran ini
        # untuk mendeteksi kondisi semua habis.
        attempts = 0

        while attempts < total:
            account = self._accounts[self._current_index]
            email = account.email

            # Hitung indeks berikutnya (akan digunakan pada pemanggilan next() berikutnya)
            next_index = (self._current_index + 1) % total

            # Deteksi wrap-around: saat kita kembali ke indeks 0, reset temporary-skipped
            # agar akun tersebut kembali masuk rotasi di putaran berikutnya.
            if next_index == 0 and self._current_index != 0:
                self._temporary_skipped.clear()

            self._current_index = next_index

            # Lewati akun yang permanent-failed
            if email in self._permanent_failed:
                attempts += 1
                continue

            # Lewati akun yang temporary-skipped untuk putaran ini
            if email in self._temporary_skipped:
                attempts += 1
                continue

            return account

        # Semua akun sudah dicoba dan tidak ada yang tersedia
        raise NoSeedAccountError(
            "Semua seed account tidak tersedia: semua akun telah gagal "
            "atau dikecualikan dari rotasi."
        )

    def mark_failed_permanent(self, email: str) -> None:
        """Kecualikan akun dari rotasi untuk seluruh run saat ini.

        Digunakan ketika login gagal karena kredensial tidak valid
        (Requirement 2.5). Akun tidak akan pernah dipilih lagi dalam
        run ini.

        Args:
            email: Alamat email akun yang akan dikecualikan secara permanen.
        """
        self._permanent_failed.add(email)
        logger.warning(
            "Seed account '%s' ditandai permanent-failed dan dikecualikan "
            "dari rotasi untuk run ini.",
            email,
        )

    def mark_failed_temporary(self, email: str) -> None:
        """Lewati akun untuk sesi ini; akun kembali di putaran berikutnya.

        Digunakan ketika Google meminta verifikasi tambahan (Requirement 2.6).
        Akun akan dilewati hingga rotasi mencapai wrap-around, setelah itu
        akun kembali tersedia.

        Args:
            email: Alamat email akun yang akan dilewati sementara.
        """
        self._temporary_skipped.add(email)
        logger.warning(
            "Seed account '%s' ditandai temporary-failed dan akan dilewati "
            "untuk sesi ini; akun akan kembali di putaran berikutnya.",
            email,
        )

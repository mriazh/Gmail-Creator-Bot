"""
CredentialStore — komponen penyimpanan kredensial untuk Gmail Creator Bot.

Menyimpan kredensial akun Gmail yang berhasil dibuat ke file ``hasil_akun.txt``
dalam format ``email|password|YYYY-MM-DD HH:MM:SS`` (mode append, UTF-8).

Jika penulisan ke file gagal, kredensial ditampilkan di console dan dicatat
ke Logger dengan level ERROR agar tidak hilang (Requirement 8.5).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from bot_logger import BotLogger


class CredentialStore:
    """Menyimpan kredensial akun Gmail ke file ``hasil_akun.txt``.

    Setiap akun disimpan pada baris baru dalam format::

        email|password|YYYY-MM-DD HH:MM:SS

    File ditulis dengan mode append dan encoding UTF-8 sehingga data
    yang sudah ada sebelumnya tidak tertimpa (Requirement 8.2, 8.4).

    Args:
        storage_path: Path ke file penyimpanan kredensial.
            Default ``hasil_akun.txt``.
        logger: Instance :class:`~bot_logger.BotLogger` untuk mencatat error.
            Boleh ``None`` jika logging tidak diperlukan.
    """

    COMPONENT = "CredentialStore"
    DEFAULT_PATH = "hasil_akun.txt"

    def __init__(
        self,
        storage_path: str = DEFAULT_PATH,
        logger: Optional[BotLogger] = None,
    ) -> None:
        self._storage_path = storage_path
        self._logger = logger

    def save(self, email: str, password: str, created_at: datetime) -> None:
        """Simpan satu set kredensial ke file penyimpanan.

        Menambahkan baris baru dalam format ``email|password|YYYY-MM-DD HH:MM:SS``
        ke file ``hasil_akun.txt`` menggunakan mode append dan encoding UTF-8.

        Jika penulisan gagal karena error sistem (misalnya permission denied
        atau disk penuh), kredensial lengkap ditampilkan di console dan
        dicatat ke Logger dengan level ERROR agar tidak hilang
        (Requirement 8.5).

        Args:
            email: Alamat email akun Gmail yang berhasil dibuat.
            password: Password akun Gmail.
            created_at: Waktu pembuatan akun.
        """
        timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{email}|{password}|{timestamp}"

        try:
            # Requirement 8.1: format email|password|YYYY-MM-DD HH:MM:SS
            # Requirement 8.2: mode append agar data lama tidak tertimpa
            # Requirement 8.4: encoding UTF-8
            with open(self._storage_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception as exc:
            # Requirement 8.5: jika penulisan gagal, tampilkan di console
            # dan catat ke Logger dengan level ERROR
            fallback_message = (
                f"[CREDENTIAL FALLBACK] Gagal menyimpan ke file. "
                f"Kredensial: {line}"
            )
            print(fallback_message)

            error_message = (
                f"Gagal menulis ke '{self._storage_path}': {exc}. "
                f"Kredensial: {line}"
            )
            if self._logger is not None:
                self._logger.error(self.COMPONENT, error_message)

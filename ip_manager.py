"""
IPManager — komponen manajemen dan validasi rotasi IP untuk Gmail Creator Bot.

Bertanggung jawab untuk:
- Memeriksa alamat IP publik saat ini via api.ipify.org
- Memandu pengguna melakukan rotasi IP secara manual
- Mencatat riwayat pergantian IP ke ip_history.log

Mendefinisikan exception IPCheckError untuk kegagalan pengecekan IP.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Optional

import requests

from bot_logger import BotLogger


class IPCheckError(Exception):
    """Raised ketika pengecekan IP publik gagal (timeout, koneksi error, dll.)."""


class IPManager:
    """Mengelola pengecekan dan rotasi IP publik untuk Gmail Creator Bot.

    Menggunakan ``https://api.ipify.org`` untuk mendapatkan IP publik saat ini.
    Riwayat pergantian IP dicatat ke ``ip_history.log`` dalam format:
    ``old_ip -> new_ip @ ISO8601_timestamp``

    Args:
        logger: Instance :class:`~bot_logger.BotLogger` untuk pencatatan log.
            Jika ``None``, logger baru dibuat dengan konfigurasi default.
        history_path: Path ke file riwayat IP. Default ``ip_history.log``.
    """

    CHECK_URL = "https://api.ipify.org"
    TIMEOUT_SECONDS = 10
    MAX_ROTATION_ATTEMPTS = 10
    COMPONENT = "IPManager"

    def __init__(
        self,
        logger: Optional[BotLogger] = None,
        history_path: str = "ip_history.log",
    ) -> None:
        self._logger = logger if logger is not None else BotLogger()
        self._history_path = history_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_ip(self) -> str:
        """Ambil alamat IP publik saat ini dari api.ipify.org.

        Melakukan GET request ke ``https://api.ipify.org`` dengan timeout
        10 detik. Mengembalikan IP sebagai string jika berhasil.

        Returns:
            Alamat IP publik saat ini sebagai string (misal ``"203.0.113.42"``).

        Raises:
            IPCheckError: Jika request gagal karena timeout, koneksi error,
                atau respons tidak valid.
        """
        try:
            response = requests.get(
                self.CHECK_URL,
                timeout=self.TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            ip = response.text.strip()
            if not ip:
                raise IPCheckError("Respons dari api.ipify.org kosong")
            return ip
        except requests.exceptions.Timeout as exc:
            raise IPCheckError(
                f"Timeout ({self.TIMEOUT_SECONDS}s) saat menghubungi {self.CHECK_URL}"
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise IPCheckError(
                f"Koneksi ke {self.CHECK_URL} gagal: {exc}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise IPCheckError(
                f"Request ke {self.CHECK_URL} gagal: {exc}"
            ) from exc

    def prompt_ip_rotation(self, current_ip: str) -> str:
        """Tampilkan notifikasi rotasi IP dan verifikasi IP telah berubah.

        Menampilkan IP saat ini ke console, menginstruksikan pengguna untuk
        mengganti IP, lalu menunggu pengguna menekan ENTER. Setelah ENTER
        ditekan, memverifikasi bahwa IP telah berubah. Proses ini diulang
        hingga maksimal 10 kali jika IP belum berubah.

        Jika ``api.ipify.org`` tidak dapat dijangkau saat verifikasi,
        mencatat ERROR dan meminta konfirmasi manual dari pengguna.

        Args:
            current_ip: Alamat IP publik sebelum rotasi.

        Returns:
            Alamat IP publik baru setelah rotasi berhasil dikonfirmasi.

        Raises:
            SystemExit: Jika IP tidak berubah setelah 10 kali percobaan.
        """
        print("\n" + "=" * 60)
        print("⚠  ROTASI IP DIPERLUKAN")
        print("=" * 60)
        print(f"IP saat ini  : {current_ip}")
        print("Instruksi    : Ganti IP Anda (VPN/proxy/hotspot), lalu tekan ENTER.")
        print("=" * 60)

        for attempt in range(1, self.MAX_ROTATION_ATTEMPTS + 1):
            input(f"\n[Percobaan {attempt}/{self.MAX_ROTATION_ATTEMPTS}] Tekan ENTER setelah mengganti IP... ")

            # Coba dapatkan IP baru
            try:
                new_ip = self.get_current_ip()
            except IPCheckError as exc:
                # Requirement 7.8 — api.ipify.org tidak terjangkau
                self._logger.error(
                    self.COMPONENT,
                    f"Pengecekan IP gagal: {exc}",
                )
                print(
                    f"\n❌ Pengecekan IP gagal: {exc}\n"
                    "   Tidak dapat memverifikasi perubahan IP secara otomatis."
                )
                confirm = input("   Apakah Anda yakin IP sudah berganti? (y/n): ").strip().lower()
                if confirm == "y":
                    self._logger.info(
                        self.COMPONENT,
                        "Pengguna mengkonfirmasi pergantian IP secara manual (pengecekan otomatis gagal).",
                    )
                    # Kembalikan placeholder karena tidak bisa verifikasi otomatis
                    return "UNKNOWN (dikonfirmasi manual)"
                else:
                    print("   Silakan coba ganti IP kembali.")
                    continue

            # Verifikasi IP berubah
            if new_ip != current_ip:
                # Requirement 7.6 — IP berhasil berubah
                self._logger.info(
                    self.COMPONENT,
                    f"IP berhasil berubah: {current_ip} -> {new_ip}",
                )
                print(f"\n✅ IP berhasil berubah: {current_ip} → {new_ip}")
                return new_ip
            else:
                # Requirement 7.5 — IP belum berubah
                remaining = self.MAX_ROTATION_ATTEMPTS - attempt
                if remaining > 0:
                    print(
                        f"\n⚠  IP belum berubah (masih {new_ip}). "
                        f"Sisa percobaan: {remaining}."
                    )
                    self._logger.warning(
                        self.COMPONENT,
                        f"IP belum berubah setelah percobaan {attempt}: {new_ip}",
                    )

        # Requirement 7.5 — IP tidak berubah setelah 10x → hentikan eksekusi
        self._logger.error(
            self.COMPONENT,
            f"IP tidak berubah setelah {self.MAX_ROTATION_ATTEMPTS} percobaan. Menghentikan eksekusi.",
        )
        print(
            f"\n❌ IP tidak berubah setelah {self.MAX_ROTATION_ATTEMPTS} percobaan. "
            "Bot dihentikan."
        )
        sys.exit(1)

    def log_ip_change(self, old_ip: str, new_ip: str) -> None:
        """Catat pergantian IP ke file ip_history.log.

        Menambahkan satu baris ke ``ip_history.log`` dalam format:
        ``old_ip -> new_ip @ ISO8601_timestamp``

        Timestamp menggunakan format ISO 8601 dengan timezone UTC.

        Args:
            old_ip: Alamat IP sebelum pergantian.
            new_ip: Alamat IP setelah pergantian.
        """
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        entry = f"{old_ip} -> {new_ip} @ {timestamp}\n"

        try:
            with open(self._history_path, "a", encoding="utf-8") as fh:
                fh.write(entry)
        except OSError as exc:
            self._logger.error(
                self.COMPONENT,
                f"Gagal menulis ke {self._history_path}: {exc}",
            )
            # Tetap catat ke log utama agar informasi tidak hilang
            self._logger.info(
                self.COMPONENT,
                f"Riwayat IP (tidak tersimpan ke file): {old_ip} -> {new_ip} @ {timestamp}",
            )
            return

        # Requirement 7.6 & 7.7 — catat ke Logger dengan level INFO
        self._logger.info(
            self.COMPONENT,
            f"Riwayat IP dicatat: {old_ip} -> {new_ip} @ {timestamp}",
        )

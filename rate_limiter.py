"""
Rate Limiter untuk Gmail Creator Bot.

Mengatur jeda waktu antar sesi untuk menghindari deteksi pola otomatis
oleh sistem keamanan Google.
"""

import random
import sys
import time


class RateLimiter:
    """Mengatur jeda waktu antar sesi pembuatan akun Gmail.

    Melacak jumlah sesi secara internal untuk memicu jeda tambahan
    setiap 5 sesi, dan memperingatkan pengguna jika bot berjalan
    terlalu lama tanpa henti.

    Attributes:
        _session_count: Jumlah sesi yang telah dijalankan sejak startup.
        _start_time: Waktu startup bot (epoch seconds).
        EXTENDED_BREAK_INTERVAL: Setiap berapa sesi jeda tambahan diterapkan.
        EXTENDED_BREAK_MIN: Durasi minimum jeda tambahan (detik).
        EXTENDED_BREAK_MAX: Durasi maksimum jeda tambahan (detik).
        MAX_RUNTIME_SECONDS: Batas waktu berjalan berturut-turut sebelum peringatan.
    """

    EXTENDED_BREAK_INTERVAL: int = 5
    EXTENDED_BREAK_MIN: int = 60
    EXTENDED_BREAK_MAX: int = 300
    MAX_RUNTIME_SECONDS: int = 7200  # 2 jam

    def __init__(self) -> None:
        self._session_count: int = 0
        self._start_time: float = time.time()

    def wait_between_sessions(self, delay_min: int, delay_max: int) -> None:
        """Terapkan jeda acak antara sesi dengan countdown di console.

        Jeda dipilih secara acak dalam rentang [delay_min, delay_max] detik.
        Countdown diperbarui setiap detik di baris yang sama menggunakan
        carriage return (\\r).

        Setelah jeda selesai, sesi dihitung dan:
        - Jika sudah 5 sesi (kelipatan EXTENDED_BREAK_INTERVAL), panggil
          wait_extended_break() secara otomatis.
        - Jika bot berjalan >7200 detik, tampilkan peringatan.

        Args:
            delay_min: Jeda minimum dalam detik (1–3600).
            delay_max: Jeda maksimum dalam detik (1–3600, >= delay_min).
        """
        delay = random.randint(delay_min, delay_max)
        self._countdown(delay, label="Jeda antar sesi")

        self._session_count += 1

        # Periksa apakah bot sudah berjalan terlalu lama
        self._check_runtime_warning()

        # Terapkan jeda tambahan setiap 5 sesi
        if self._session_count % self.EXTENDED_BREAK_INTERVAL == 0:
            self.wait_extended_break()

    def wait_extended_break(self) -> None:
        """Terapkan jeda tambahan acak antara 60–300 detik setiap 5 sesi.

        Mensimulasikan pola istirahat manusia. Countdown ditampilkan di
        console dan diperbarui setiap detik.
        """
        delay = random.randint(self.EXTENDED_BREAK_MIN, self.EXTENDED_BREAK_MAX)
        print(
            f"\n[RateLimiter] Jeda tambahan setelah {self._session_count} sesi..."
        )
        self._countdown(delay, label="Jeda tambahan")

    def _countdown(self, seconds: int, label: str = "Menunggu") -> None:
        """Tampilkan countdown di console yang diperbarui setiap detik.

        Menggunakan carriage return (\\r) agar countdown tampil di baris
        yang sama tanpa menambah baris baru.

        Args:
            seconds: Jumlah detik untuk countdown.
            label: Label yang ditampilkan sebelum sisa waktu.
        """
        for remaining in range(seconds, 0, -1):
            print(f"\r{label}: {remaining} detik tersisa...  ", end="", flush=True)
            time.sleep(1)
        # Bersihkan baris countdown setelah selesai
        print(f"\r{label}: selesai.                          ")

    def _check_runtime_warning(self) -> None:
        """Tampilkan peringatan jika bot berjalan lebih dari 7200 detik.

        Peringatan ditampilkan ke stdout agar terlihat oleh pengguna.
        """
        elapsed = time.time() - self._start_time
        if elapsed > self.MAX_RUNTIME_SECONDS:
            elapsed_hours = elapsed / 3600
            print(
                f"\n[PERINGATAN] Bot telah berjalan selama {elapsed_hours:.1f} jam "
                f"({elapsed:.0f} detik) berturut-turut. "
                "Disarankan untuk menghentikan bot dan melanjutkan di lain waktu "
                "agar tidak terdeteksi sebagai aktivitas otomatis.",
                file=sys.stdout,
            )

"""
BotLogger — komponen logging terpusat untuk Gmail Creator Bot.

Menulis log ke `bot_activity.log` (mode append, UTF-8) dengan format:
    [YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan

Jika penulisan ke file gagal, fallback ke stderr agar informasi tidak hilang.
"""

from __future__ import annotations

import sys
import traceback
from collections import Counter
from datetime import datetime
from typing import Optional

from models import BatchStats


class BotLogger:
    """Logger terpusat untuk semua aktivitas Gmail Creator Bot.

    Format log: ``[YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan``

    Log ditulis ke ``bot_activity.log`` (mode append, UTF-8).
    Jika penulisan ke file gagal, log dikirim ke stderr sebagai fallback.

    Args:
        log_path: Path ke file log. Default ``bot_activity.log``.
    """

    FORMAT = "[{timestamp}] [{level}] [{component}] {message}"
    LOG_PATH = "bot_activity.log"

    def __init__(self, log_path: str = LOG_PATH) -> None:
        self._log_path = log_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _format_line(self, level: str, component: str, message: str) -> str:
        """Buat satu baris log sesuai format yang ditentukan."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.FORMAT.format(
            timestamp=timestamp,
            level=level,
            component=component,
            message=message,
        )

    def _write(self, line: str) -> None:
        """Tulis satu baris ke file log; fallback ke stderr jika gagal."""
        try:
            with open(self._log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            # Requirement 9.7 — fallback ke stderr jika file tidak bisa ditulis
            print(line, file=sys.stderr)

    def _log(
        self,
        level: str,
        component: str,
        message: str,
        exc_info: bool = False,
    ) -> None:
        """Tulis satu entri log, opsional dengan stack trace."""
        line = self._format_line(level, component, message)
        self._write(line)

        if exc_info:
            # Sertakan stack trace sebagai baris-baris tambahan di log
            tb = traceback.format_exc()
            if tb and tb.strip() != "NoneType: None":
                for tb_line in tb.rstrip().splitlines():
                    self._write(tb_line)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def info(self, component: str, message: str) -> None:
        """Catat pesan level INFO.

        Args:
            component: Nama komponen yang mencatat log (misal ``"SeedRotator"``).
            message: Pesan log.
        """
        self._log("INFO", component, message)

    def warning(self, component: str, message: str) -> None:
        """Catat pesan level WARNING.

        Args:
            component: Nama komponen yang mencatat log.
            message: Pesan log.
        """
        self._log("WARNING", component, message)

    def error(
        self,
        component: str,
        message: str,
        exc_info: bool = False,
    ) -> None:
        """Catat pesan level ERROR, opsional dengan stack trace.

        Args:
            component: Nama komponen yang mencatat log.
            message: Pesan log.
            exc_info: Jika ``True``, sertakan stack trace dari exception aktif.
        """
        self._log("ERROR", component, message, exc_info=exc_info)

    def summary(self, stats: BatchStats) -> None:
        """Tampilkan ringkasan batch ke console dan catat ke log.

        Menampilkan:
        - Total sesi yang dijalankan
        - Jumlah sesi berhasil
        - Jumlah sesi gagal
        - Top-3 alasan kegagalan terbanyak (jika ada)

        Args:
            stats: Objek :class:`~models.BatchStats` berisi statistik batch.
        """
        lines = [
            "=" * 50,
            "RINGKASAN BATCH",
            "=" * 50,
            f"Total sesi    : {stats.total_sessions}",
            f"Berhasil      : {stats.successful}",
            f"Gagal         : {stats.failed}",
        ]

        if stats.failure_reasons:
            lines.append("Top-3 alasan gagal:")
            top3 = stats.failure_reasons.most_common(3)
            for rank, (reason, count) in enumerate(top3, start=1):
                lines.append(f"  {rank}. {reason} ({count}x)")
        else:
            lines.append("Top-3 alasan gagal: (tidak ada kegagalan)")

        lines.append("=" * 50)

        summary_text = "\n".join(lines)
        print(summary_text)

        # Juga catat ringkasan ke file log
        self.info("BotLogger", f"Batch selesai — total={stats.total_sessions}, "
                               f"berhasil={stats.successful}, gagal={stats.failed}")
        if stats.failure_reasons:
            top3_str = ", ".join(
                f"{r}({c}x)" for r, c in stats.failure_reasons.most_common(3)
            )
            self.info("BotLogger", f"Top-3 alasan gagal: {top3_str}")

"""
Data models untuk Gmail Creator Bot.

Mendefinisikan semua dataclass yang digunakan di seluruh sistem:
BotConfig, SeedAccount, Identity, SessionResult, BatchStats,
FarmingResult, CreationResult.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class SeedAccount:
    """Akun Gmail pancingan yang digunakan untuk pemanasan cookie.

    Attributes:
        email: Alamat email seed account (maks 254 karakter).
        password: Password seed account (maks 128 karakter).
    """

    email: str
    password: str


@dataclass
class BotConfig:
    """Konfigurasi utama bot yang dimuat dari config.json.

    Attributes:
        seed_accounts: Daftar seed account (maks 100 entri).
        phone_numbers: Daftar nomor HP untuk verifikasi (maks 100 entri).
        accounts_per_ip_rotation: Jumlah akun per rotasi IP (rentang valid: 1–50).
        delay_min: Jeda minimum antar sesi dalam detik (rentang valid: 1–3600).
        delay_max: Jeda maksimum antar sesi dalam detik (rentang valid: 1–3600, >= delay_min).
        total_accounts: Total akun yang ingin dibuat (rentang valid: 1–10000).
        faker_locale: Locale Faker untuk generasi identitas (default: "en_US").
    """

    seed_accounts: list[SeedAccount]
    phone_numbers: list[str]
    accounts_per_ip_rotation: int
    delay_min: int
    delay_max: int
    total_accounts: int
    faker_locale: str = "en_US"


@dataclass
class Identity:
    """Identitas palsu yang dihasilkan oleh IdentityGenerator.

    Attributes:
        first_name: Nama depan.
        last_name: Nama belakang.
        birth_date: Tanggal lahir (usia 18–40 tahun dari tanggal saat ini).
        username: Username Gmail (6–30 karakter, hanya huruf/angka/titik).
        password: Password akun (≥12 karakter, campuran huruf besar/kecil/angka/simbol).
        email: Alamat email lengkap (username + "@gmail.com").
    """

    first_name: str
    last_name: str
    birth_date: date
    username: str
    password: str
    email: str


@dataclass
class SessionResult:
    """Hasil dari satu sesi pembuatan akun.

    Attributes:
        session_number: Nomor urut sesi.
        success: True jika akun berhasil dibuat.
        email_created: Alamat email yang berhasil dibuat, atau None jika gagal.
        seed_account_used: Email seed account yang digunakan pada sesi ini.
        failure_phase: Fase kegagalan jika sesi gagal. Salah satu dari:
            INIT | SEED_LOGIN | COOKIE_FARMING | IDENTITY_GEN | FORM_FILL | VERIFICATION
        error_message: Pesan error jika sesi gagal, atau None jika berhasil.
        duration_seconds: Durasi sesi dalam satuan detik.
    """

    session_number: int
    success: bool
    email_created: Optional[str]
    seed_account_used: str
    failure_phase: Optional[str]
    error_message: Optional[str]
    duration_seconds: float


@dataclass
class BatchStats:
    """Statistik keseluruhan dari satu batch eksekusi bot.

    Attributes:
        total_sessions: Total sesi yang dijalankan.
        successful: Jumlah sesi yang berhasil membuat akun.
        failed: Jumlah sesi yang gagal.
        failure_reasons: Counter alasan kegagalan untuk menampilkan top-3.
        start_time: Waktu mulai batch.
        end_time: Waktu selesai batch, atau None jika masih berjalan.
    """

    total_sessions: int
    successful: int
    failed: int
    failure_reasons: Counter[str]
    start_time: datetime
    end_time: Optional[datetime] = None


@dataclass
class FarmingResult:
    """Hasil dari fase cookie farming.

    Attributes:
        success: True jika farming berhasil diselesaikan.
        domains_visited: Daftar domain yang berhasil dikunjungi.
        total_duration_seconds: Total durasi farming dalam detik.
        error_message: Pesan error jika farming gagal, atau None jika berhasil.
    """

    success: bool
    domains_visited: list[str]
    total_duration_seconds: float
    error_message: Optional[str] = None


@dataclass
class CreationResult:
    """Hasil dari fase pembuatan akun Gmail.

    Attributes:
        success: True jika akun berhasil dibuat.
        email: Alamat email akun yang dibuat, atau None jika gagal.
        failure_reason: Alasan kegagalan jika pembuatan gagal, atau None jika berhasil.
    """

    success: bool
    email: Optional[str] = None
    failure_reason: Optional[str] = None

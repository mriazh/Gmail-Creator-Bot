"""
Property-based tests untuk Gmail Creator Bot.

Menggunakan Hypothesis untuk memverifikasi properti universal
yang harus berlaku untuk semua input valid.

Semua test dijalankan dari project root:
    pytest tests/property/test_properties.py
"""

from __future__ import annotations

import sys
import os

# Pastikan project root ada di sys.path agar modul sumber bisa diimpor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from config_loader import ConfigLoader


# ---------------------------------------------------------------------------
# Strategi Hypothesis untuk menghasilkan nilai tidak valid per field
# ---------------------------------------------------------------------------

# Nilai tidak valid untuk accounts_per_ip_rotation (int, range 1–50)
invalid_accounts_per_ip = st.one_of(
    st.integers(max_value=0),           # di bawah minimum
    st.integers(min_value=51),          # di atas maksimum
    st.floats(allow_nan=False),         # tipe salah: float
    st.text(),                          # tipe salah: string
    st.booleans(),                      # bool dianggap tidak valid (isinstance bool check)
    st.none(),                          # None
)

# Nilai tidak valid untuk delay_min (int, range 1–3600)
invalid_delay_min = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=3601),
    st.floats(allow_nan=False),
    st.text(),
    st.booleans(),
    st.none(),
)

# Nilai tidak valid untuk delay_max (int, range 1–3600)
invalid_delay_max = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=3601),
    st.floats(allow_nan=False),
    st.text(),
    st.booleans(),
    st.none(),
)

# Nilai tidak valid untuk total_accounts (int, range 1–10000)
invalid_total_accounts = st.one_of(
    st.integers(max_value=0),
    st.integers(min_value=10001),
    st.floats(allow_nan=False),
    st.text(),
    st.booleans(),
    st.none(),
)

# Nilai tidak valid untuk seed_accounts (list, max 100 entri)
invalid_seed_accounts = st.one_of(
    st.text(),                                          # tipe salah: string
    st.integers(),                                      # tipe salah: int
    st.booleans(),                                      # tipe salah: bool
    st.none(),                                          # None
    st.lists(st.integers(), min_size=101, max_size=110),  # list terlalu panjang
)

# Nilai tidak valid untuk phone_numbers (list, max 100 entri)
invalid_phone_numbers = st.one_of(
    st.text(),
    st.integers(),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), min_size=101, max_size=110),
)

# Nilai tidak valid untuk faker_locale (harus string jika ada)
invalid_faker_locale = st.one_of(
    st.integers(),
    st.booleans(),
    st.none(),
    st.floats(allow_nan=False),
    st.lists(st.text()),
)


def _valid_base_config() -> dict:
    """Kembalikan config yang sepenuhnya valid sebagai titik awal."""
    return {
        "seed_accounts": [],
        "phone_numbers": [],
        "accounts_per_ip_rotation": 5,
        "delay_min": 30,
        "delay_max": 90,
        "total_accounts": 10,
        "faker_locale": "en_US",
    }


# ---------------------------------------------------------------------------
# Property 8: Validasi config mendeteksi semua field tidak valid tanpa terkecuali
# Feature: gmail-creator-bot, Property 8: Validasi config mendeteksi semua field tidak valid tanpa terkecuali
# Validates: Requirements 11.5
# ---------------------------------------------------------------------------

@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_accounts_per_ip)
def test_property_8_config_validation_accounts_per_ip_rotation(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field accounts_per_ip_rotation,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["accounts_per_ip_rotation"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal accounts_per_ip_rotation={invalid_val!r} tidak valid"
    )
    assert "accounts_per_ip_rotation" in invalid_fields, (
        f"'accounts_per_ip_rotation' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_delay_min)
def test_property_8_config_validation_delay_min(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field delay_min,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["delay_min"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal delay_min={invalid_val!r} tidak valid"
    )
    assert "delay_min" in invalid_fields, (
        f"'delay_min' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_delay_max)
def test_property_8_config_validation_delay_max(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field delay_max,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["delay_max"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal delay_max={invalid_val!r} tidak valid"
    )
    assert "delay_max" in invalid_fields, (
        f"'delay_max' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_total_accounts)
def test_property_8_config_validation_total_accounts(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field total_accounts,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["total_accounts"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal total_accounts={invalid_val!r} tidak valid"
    )
    assert "total_accounts" in invalid_fields, (
        f"'total_accounts' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_seed_accounts)
def test_property_8_config_validation_seed_accounts(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field seed_accounts,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["seed_accounts"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal seed_accounts={invalid_val!r} tidak valid"
    )
    assert "seed_accounts" in invalid_fields, (
        f"'seed_accounts' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_phone_numbers)
def test_property_8_config_validation_phone_numbers(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field phone_numbers,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["phone_numbers"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal phone_numbers={invalid_val!r} tidak valid"
    )
    assert "phone_numbers" in invalid_fields, (
        f"'phone_numbers' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(invalid_val=invalid_faker_locale)
def test_property_8_config_validation_faker_locale(invalid_val):
    """
    **Validates: Requirements 11.5**

    Property 8: Untuk setiap nilai tidak valid pada field faker_locale (non-string),
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    config["faker_locale"] = invalid_val

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal faker_locale={invalid_val!r} tidak valid"
    )
    assert "faker_locale" in invalid_fields, (
        f"'faker_locale' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    missing_field=st.sampled_from([
        "seed_accounts",
        "phone_numbers",
        "accounts_per_ip_rotation",
        "delay_min",
        "delay_max",
        "total_accounts",
    ])
)
def test_property_8_config_validation_missing_required_field(missing_field):
    """
    **Validates: Requirements 11.5**

    Property 8: Jika salah satu field wajib tidak ada dalam config,
    ConfigLoader.validate() harus mengembalikan list yang mengandung field tersebut.
    """
    config = _valid_base_config()
    del config[missing_field]

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert len(invalid_fields) > 0, (
        f"validate() mengembalikan list kosong padahal field wajib '{missing_field}' tidak ada"
    )
    assert missing_field in invalid_fields, (
        f"'{missing_field}' tidak ada dalam daftar field invalid: {invalid_fields}"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    bad_accounts_per_ip=st.one_of(st.integers(max_value=0), st.integers(min_value=51)),
    bad_total_accounts=st.one_of(st.integers(max_value=0), st.integers(min_value=10001)),
)
def test_property_8_config_validation_multiple_invalid_fields_all_reported(
    bad_accounts_per_ip, bad_total_accounts
):
    """
    **Validates: Requirements 11.5**

    Property 8: Ketika beberapa field sekaligus tidak valid,
    ConfigLoader.validate() harus melaporkan SEMUA field yang tidak valid —
    tidak ada yang terlewat.
    """
    config = _valid_base_config()
    config["accounts_per_ip_rotation"] = bad_accounts_per_ip
    config["total_accounts"] = bad_total_accounts

    loader = ConfigLoader()
    invalid_fields = loader.validate(config)

    assert "accounts_per_ip_rotation" in invalid_fields, (
        f"'accounts_per_ip_rotation' tidak dilaporkan sebagai invalid. "
        f"Nilai: {bad_accounts_per_ip!r}. Daftar invalid: {invalid_fields}"
    )
    assert "total_accounts" in invalid_fields, (
        f"'total_accounts' tidak dilaporkan sebagai invalid. "
        f"Nilai: {bad_total_accounts!r}. Daftar invalid: {invalid_fields}"
    )


# ---------------------------------------------------------------------------
# Property 11: Format log selalu mengikuti pola yang ditentukan
# Feature: gmail-creator-bot, Property 11: Format log selalu mengikuti pola yang ditentukan
# Validates: Requirements 9.1
# ---------------------------------------------------------------------------

import re
import tempfile

from bot_logger import BotLogger

# Pola format log: [YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan
_LOG_FORMAT_PATTERN = re.compile(
    r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \[.+?\] \[.+?\] .*$"
)

# Strategi untuk teks komponen dan pesan — karakter printable agar log terbaca
_printable_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "S", "Zs")),
    min_size=1,
    max_size=100,
)

_log_levels = st.sampled_from(["INFO", "WARNING", "ERROR"])


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(component=_printable_text, message=_printable_text, level=_log_levels)
def test_property_11_log_format(component: str, message: str, level: str) -> None:
    """
    **Validates: Requirements 9.1**

    Property 11: Format log selalu mengikuti pola yang ditentukan.

    For any pemanggilan Logger (info, warning, atau error) dengan komponen C,
    level L, dan pesan M, baris yang ditulis ke bot_activity.log harus persis
    mengikuti format [YYYY-MM-DD HH:MM:SS] [L] [C] M — tidak ada variasi
    format yang diizinkan.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False, encoding="utf-8"
    ) as tmp:
        tmp_path = tmp.name

    try:
        logger = BotLogger(log_path=tmp_path)

        # Panggil metode log sesuai level yang di-generate
        if level == "INFO":
            logger.info(component, message)
        elif level == "WARNING":
            logger.warning(component, message)
        else:  # ERROR
            logger.error(component, message)

        # Baca baris yang ditulis ke file log
        with open(tmp_path, encoding="utf-8") as fh:
            lines = fh.readlines()

        # Harus ada tepat satu baris yang ditulis
        assert len(lines) == 1, (
            f"Diharapkan 1 baris log, tetapi ditemukan {len(lines)} baris. "
            f"Komponen={component!r}, Pesan={message!r}, Level={level!r}"
        )

        log_line = lines[0].rstrip("\n")

        # Verifikasi format keseluruhan menggunakan regex
        assert _LOG_FORMAT_PATTERN.match(log_line), (
            f"Baris log tidak sesuai format yang ditentukan.\n"
            f"  Baris  : {log_line!r}\n"
            f"  Pola   : [YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan\n"
            f"  Input  : komponen={component!r}, pesan={message!r}, level={level!r}"
        )

        # Verifikasi level yang benar tercantum dalam baris log
        assert f"[{level}]" in log_line, (
            f"Level [{level}] tidak ditemukan dalam baris log: {log_line!r}"
        )

        # Verifikasi komponen yang benar tercantum dalam baris log
        assert f"[{component}]" in log_line, (
            f"Komponen [{component}] tidak ditemukan dalam baris log: {log_line!r}"
        )

        # Verifikasi pesan tercantum dalam baris log
        assert log_line.endswith(message), (
            f"Pesan {message!r} tidak ditemukan di akhir baris log: {log_line!r}"
        )

    finally:
        # Bersihkan file sementara
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Property 5: Kredensial tersimpan secara persisten dengan format yang benar
# Feature: gmail-creator-bot, Property 5: Kredensial tersimpan secara
# persisten dengan format yang benar
# Validates: Requirements 8.1, 8.2, 8.4
# ---------------------------------------------------------------------------

import re
import tempfile
from datetime import datetime

from credential_store import CredentialStore


# Strategi untuk email-like string: local-part@domain.tld
# Menggunakan karakter yang aman untuk menghindari karakter kontrol
_safe_text = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),  # huruf besar, kecil, angka
        whitelist_characters="._-",
    ),
    min_size=1,
    max_size=30,
)

email_strategy = st.builds(
    lambda local, domain: f"{local}@{domain}.com",
    local=_safe_text,
    domain=_safe_text,
)

# Strategi untuk password: minimal 12 karakter, campuran karakter aman
password_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="!@#$%^&*()_+-=",
    ),
    min_size=12,
    max_size=64,
)

# Strategi untuk datetime: rentang yang wajar
datetime_strategy = st.datetimes(
    min_value=datetime(2000, 1, 1, 0, 0, 0),
    max_value=datetime(2099, 12, 31, 23, 59, 59),
)

# Pola regex untuk validasi format baris yang disimpan
_LINE_PATTERN = re.compile(
    r"^.+\|.+\|\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"
)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    email=email_strategy,
    password=password_strategy,
    created_at=datetime_strategy,
)
def test_property_5_credential_format(
    email: str, password: str, created_at: datetime
) -> None:
    """**Validates: Requirements 8.1, 8.4**

    For any email, password, and datetime, the saved line must be exactly
    in the format ``email|password|YYYY-MM-DD HH:MM:SS`` and the file must
    use UTF-8 encoding.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp_path = tmp.name

    try:
        store = CredentialStore(storage_path=tmp_path)
        store.save(email, password, created_at)

        # Baca kembali file dengan encoding UTF-8 (Requirement 8.4)
        with open(tmp_path, encoding="utf-8") as fh:
            content = fh.read()

        lines = content.splitlines()
        assert len(lines) == 1, (
            f"Diharapkan 1 baris, ditemukan {len(lines)}"
        )

        line = lines[0]

        # Requirement 8.1: format email|password|YYYY-MM-DD HH:MM:SS
        expected_timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S")
        expected_line = f"{email}|{password}|{expected_timestamp}"
        assert line == expected_line, (
            f"Format baris tidak sesuai.\n"
            f"  Diharapkan : {expected_line!r}\n"
            f"  Ditemukan  : {line!r}"
        )

        # Verifikasi pola regex umum
        assert _LINE_PATTERN.match(line), (
            f"Baris tidak cocok dengan pola format: {line!r}"
        )
    finally:
        os.unlink(tmp_path)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    credentials=st.lists(
        st.tuples(email_strategy, password_strategy, datetime_strategy),
        min_size=2,
        max_size=10,
    )
)
def test_property_5_credential_persistence_append(
    credentials: list[tuple[str, str, datetime]],
) -> None:
    """**Validates: Requirements 8.2, 8.4**

    For any sequence of saves, all previously saved credentials must remain
    intact (append mode — no overwrite). Each new save adds exactly one line
    without removing existing lines.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp_path = tmp.name

    try:
        store = CredentialStore(storage_path=tmp_path)

        saved_lines: list[str] = []

        for email, password, created_at in credentials:
            store.save(email, password, created_at)

            expected_timestamp = created_at.strftime("%Y-%m-%d %H:%M:%S")
            saved_lines.append(f"{email}|{password}|{expected_timestamp}")

            # Baca file setelah setiap save dan verifikasi semua baris ada
            with open(tmp_path, encoding="utf-8") as fh:
                content = fh.read()

            current_lines = content.splitlines()

            # Requirement 8.2: mode append — jumlah baris harus bertambah
            assert len(current_lines) == len(saved_lines), (
                f"Jumlah baris tidak sesuai setelah {len(saved_lines)} save.\n"
                f"  Diharapkan : {len(saved_lines)} baris\n"
                f"  Ditemukan  : {len(current_lines)} baris"
            )

            # Semua baris sebelumnya harus tetap ada (tidak tertimpa)
            for i, expected_line in enumerate(saved_lines):
                assert current_lines[i] == expected_line, (
                    f"Baris ke-{i} berubah setelah save berikutnya.\n"
                    f"  Diharapkan : {expected_line!r}\n"
                    f"  Ditemukan  : {current_lines[i]!r}"
                )
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Property 1: Username Gmail selalu memenuhi format yang valid
# Feature: gmail-creator-bot, Property 1
# Validates: Requirements 4.3, 4.4
# ---------------------------------------------------------------------------

from identity_generator import IdentityGenerator, _is_valid_gmail_username


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(st.just(None))
def test_property_1_username_format(_) -> None:
    """**Validates: Requirements 4.3, 4.4**

    Property 1: For any nama depan dan nama belakang yang diberikan ke
    IdentityGenerator, username yang dihasilkan harus memiliki panjang
    antara 6 dan 30 karakter dan hanya mengandung huruf, angka, dan titik.
    """
    gen = IdentityGenerator(locale="en_US")
    identity = gen.generate()

    username = identity.username
    assert 6 <= len(username) <= 30, (
        f"Username '{username}' panjangnya {len(username)}, di luar rentang 6–30"
    )
    assert re.match(r'^[a-zA-Z0-9.]+$', username), (
        f"Username '{username}' mengandung karakter tidak valid"
    )
    assert not username.startswith('.') and not username.endswith('.'), (
        f"Username '{username}' diawali/diakhiri titik"
    )
    assert '..' not in username, (
        f"Username '{username}' mengandung titik berurutan"
    )
    assert _is_valid_gmail_username(username), (
        f"Username '{username}' tidak lolos validasi _is_valid_gmail_username"
    )


# ---------------------------------------------------------------------------
# Property 2: Identitas yang dihasilkan selalu memenuhi semua kriteria validitas
# Feature: gmail-creator-bot, Property 2
# Validates: Requirements 4.2, 4.5
# ---------------------------------------------------------------------------

from datetime import date as date_type


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(st.just(None))
def test_property_2_identity_validity(_) -> None:
    """**Validates: Requirements 4.2, 4.5**

    Property 2: For any pemanggilan generate(), identitas yang dihasilkan harus
    memenuhi: (a) usia 18–40, (b) password >= 12 chars dengan campuran karakter,
    (c) username format Gmail valid.
    """
    gen = IdentityGenerator(locale="en_US")
    identity = gen.generate()

    # (a) Usia 18–40 tahun
    today = date_type.today()
    age_days = (today - identity.birth_date).days
    age_years = age_days / 365.0
    assert 17.5 <= age_years <= 41.0, (
        f"Usia {age_years:.1f} tahun di luar rentang 18–40"
    )

    # (b) Password >= 12 karakter, campuran
    pwd = identity.password
    assert len(pwd) >= 12, f"Password panjang {len(pwd)}, kurang dari 12"
    assert any(c.isupper() for c in pwd), "Password tidak mengandung huruf besar"
    assert any(c.islower() for c in pwd), "Password tidak mengandung huruf kecil"
    assert any(c.isdigit() for c in pwd), "Password tidak mengandung angka"
    assert any(not c.isalnum() for c in pwd), "Password tidak mengandung simbol"

    # (c) Username format Gmail
    assert _is_valid_gmail_username(identity.username)

    # Email = username@gmail.com
    assert identity.email == f"{identity.username}@gmail.com"


# ---------------------------------------------------------------------------
# Property 3: Username unik dalam satu batch eksekusi
# Feature: gmail-creator-bot, Property 3
# Validates: Requirements 4.6
# ---------------------------------------------------------------------------

@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(n=st.integers(min_value=2, max_value=20))
def test_property_3_username_uniqueness(n: int) -> None:
    """**Validates: Requirements 4.6**

    Property 3: For any batch eksekusi dengan N sesi, semua username yang
    dihasilkan harus unik — tidak ada duplikat.
    """
    gen = IdentityGenerator(locale="en_US")
    gen.reset_batch()

    usernames = []
    for _ in range(n):
        identity = gen.generate()
        usernames.append(identity.username)

    assert len(usernames) == len(set(usernames)), (
        f"Ditemukan duplikat username dalam batch {n} sesi: "
        f"{[u for u in usernames if usernames.count(u) > 1]}"
    )


# ---------------------------------------------------------------------------
# Property 4: Rotasi seed account bersifat round-robin yang konsisten
# Feature: gmail-creator-bot, Property 4
# Validates: Requirements 2.2, 2.4
# ---------------------------------------------------------------------------

from seed_account_rotator import SeedAccountRotator
from models import SeedAccount


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    k=st.integers(min_value=1, max_value=10),
    extra_rounds=st.integers(min_value=1, max_value=3),
)
def test_property_4_round_robin_rotation(k: int, extra_rounds: int) -> None:
    """**Validates: Requirements 2.2, 2.4**

    Property 4: For any daftar seed account dengan K entri valid,
    urutan pemilihan harus mengikuti round-robin sesuai urutan konfigurasi.
    """
    accounts = [
        SeedAccount(email=f"seed{i}@gmail.com", password=f"pass{i}")
        for i in range(k)
    ]
    rotator = SeedAccountRotator(accounts)

    total_calls = k * (1 + extra_rounds)
    for call_idx in range(total_calls):
        expected_idx = call_idx % k
        result = rotator.next()
        assert result.email == accounts[expected_idx].email, (
            f"Call #{call_idx}: expected seed{expected_idx}@gmail.com, "
            f"got {result.email}"
        )


# ---------------------------------------------------------------------------
# Property 6: Validasi format nomor HP konsisten dengan aturan yang ditentukan
# Feature: gmail-creator-bot, Property 6
# Validates: Requirements 6.3, 6.4
# ---------------------------------------------------------------------------

from phone_tracker import validate_phone_format

# Strategi untuk nomor yang VALID: opsional '+' diikuti 8–15 digit
_valid_phone = st.from_regex(r'^\+?\d{8,15}$', fullmatch=True)

# Strategi untuk input sembarang yang kemungkinan besar invalid
_arbitrary_text = st.text(min_size=0, max_size=30)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(phone=_valid_phone)
def test_property_6_valid_phones_accepted(phone: str) -> None:
    """**Validates: Requirements 6.3**

    Nomor HP yang memenuhi aturan (digit + opsional '+', panjang 8–15)
    harus selalu diterima.
    """
    assert validate_phone_format(phone) is True, (
        f"Nomor valid '{phone}' ditolak oleh validate_phone_format"
    )


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(text=_arbitrary_text)
def test_property_6_invalid_phones_rejected(text: str) -> None:
    """**Validates: Requirements 6.4**

    String yang TIDAK memenuhi aturan harus selalu ditolak.
    """
    # Jika text kebetulan cocok dengan pola valid, skip
    import re as _re
    if _re.match(r'^\+?\d{8,15}$', text):
        return  # kebetulan valid, skip

    assert validate_phone_format(text) is False, (
        f"String invalid '{text}' diterima oleh validate_phone_format"
    )


# ---------------------------------------------------------------------------
# Property 7: PhoneTracker mencatat penggunaan nomor secara persisten dan akurat
# Feature: gmail-creator-bot, Property 7
# Validates: Requirements 6.6, 6.7
# ---------------------------------------------------------------------------

from phone_tracker import PhoneTracker

_digit_phone = st.from_regex(r'^\+?\d{8,15}$', fullmatch=True)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(phone=_digit_phone, times=st.integers(min_value=1, max_value=5))
def test_property_7_phone_tracker_roundtrip(phone: str, times: int) -> None:
    """**Validates: Requirements 6.6, 6.7**

    Property 7: Setelah memanggil record_usage N kali, instance baru
    PhoneTracker harus mengembalikan hitungan yang tepat N.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp:
        tmp_path = tmp.name

    try:
        tracker = PhoneTracker(storage_path=tmp_path)
        for _ in range(times):
            tracker.record_usage(phone)

        # Buat instance baru untuk membuktikan persistensi
        tracker2 = PhoneTracker(storage_path=tmp_path)
        usage = tracker2.get_usage()

        assert phone in usage, f"Nomor '{phone}' tidak ada di phone_usage.json"
        assert usage[phone] == times, (
            f"Hitungan untuk '{phone}': expected {times}, got {usage[phone]}"
        )
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Property 9: Jeda antar sesi selalu dalam rentang yang dikonfigurasi
# Feature: gmail-creator-bot, Property 9
# Validates: Requirements 10.1, 10.2
# ---------------------------------------------------------------------------

from unittest.mock import patch
from rate_limiter import RateLimiter


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    delay_min=st.integers(min_value=1, max_value=100),
    delay_max=st.integers(min_value=1, max_value=100),
)
def test_property_9_rate_limiter_range(delay_min: int, delay_max: int) -> None:
    """**Validates: Requirements 10.1, 10.2**

    Property 9: Setiap jeda yang diterapkan oleh RateLimiter harus
    berada dalam rentang [delay_min, delay_max].
    """
    if delay_min > delay_max:
        delay_min, delay_max = delay_max, delay_min

    captured_delays: list[int] = []

    original_countdown = RateLimiter._countdown

    def mock_countdown(self_rl, seconds, label="Menunggu"):
        captured_delays.append(seconds)
        # Skip actual sleep

    with patch.object(RateLimiter, '_countdown', mock_countdown):
        rl = RateLimiter()
        rl.wait_between_sessions(delay_min, delay_max)

    assert len(captured_delays) >= 1, "Tidak ada delay yang tercatat"
    main_delay = captured_delays[0]
    assert delay_min <= main_delay <= delay_max, (
        f"Delay {main_delay} di luar rentang [{delay_min}, {delay_max}]"
    )

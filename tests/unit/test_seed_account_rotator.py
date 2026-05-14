"""
Unit tests untuk SeedAccountRotator.

Requirements: 2.2, 2.4, 2.5, 2.6, 2.7, 2.8
"""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from models import SeedAccount
from seed_account_rotator import SeedAccountRotator, NoSeedAccountError


class TestRoundRobin:
    """Test: round-robin melewati seluruh daftar dan kembali ke awal."""

    def test_single_account_repeats(self):
        accounts = [SeedAccount(email="a@gmail.com", password="pass")]
        rotator = SeedAccountRotator(accounts)
        for _ in range(5):
            assert rotator.next().email == "a@gmail.com"

    def test_three_accounts_round_robin(self):
        accounts = [
            SeedAccount(email=f"seed{i}@gmail.com", password=f"pass{i}")
            for i in range(3)
        ]
        rotator = SeedAccountRotator(accounts)
        expected = ["seed0@gmail.com", "seed1@gmail.com", "seed2@gmail.com",
                     "seed0@gmail.com", "seed1@gmail.com", "seed2@gmail.com"]
        for exp in expected:
            assert rotator.next().email == exp


class TestPermanentFailed:
    """Test: akun permanent-failed tidak muncul di rotasi berikutnya."""

    def test_permanent_failed_excluded(self):
        accounts = [
            SeedAccount(email="a@gmail.com", password="pass1"),
            SeedAccount(email="b@gmail.com", password="pass2"),
            SeedAccount(email="c@gmail.com", password="pass3"),
        ]
        rotator = SeedAccountRotator(accounts)

        # Ambil pertama (a), lalu mark permanent
        result = rotator.next()
        assert result.email == "a@gmail.com"
        rotator.mark_failed_permanent("a@gmail.com")

        # Selanjutnya harus b dan c, tidak pernah a
        for _ in range(6):
            result = rotator.next()
            assert result.email != "a@gmail.com"


class TestTemporaryFailed:
    """Test: akun temporary-failed kembali di putaran berikutnya."""

    def test_temporary_failed_skipped_then_returns(self):
        accounts = [
            SeedAccount(email="a@gmail.com", password="pass1"),
            SeedAccount(email="b@gmail.com", password="pass2"),
        ]
        rotator = SeedAccountRotator(accounts)

        # Ambil a, mark temporary
        result = rotator.next()
        assert result.email == "a@gmail.com"
        rotator.mark_failed_temporary("a@gmail.com")

        # Berikutnya harus b (a di-skip)
        result = rotator.next()
        assert result.email == "b@gmail.com"


class TestAllAccountsExhausted:
    """Test: semua akun habis → raise NoSeedAccountError."""

    def test_empty_list_raises(self):
        rotator = SeedAccountRotator([])
        with pytest.raises(NoSeedAccountError):
            rotator.next()

    def test_all_permanent_failed_raises(self):
        accounts = [
            SeedAccount(email="a@gmail.com", password="pass1"),
            SeedAccount(email="b@gmail.com", password="pass2"),
        ]
        rotator = SeedAccountRotator(accounts)
        rotator.mark_failed_permanent("a@gmail.com")
        rotator.mark_failed_permanent("b@gmail.com")

        with pytest.raises(NoSeedAccountError):
            rotator.next()


class TestInvalidEntries:
    """Test: entri tanpa email/password dilewati dengan WARNING."""

    def test_empty_email_skipped(self):
        accounts = [
            SeedAccount(email="", password="pass1"),
            SeedAccount(email="valid@gmail.com", password="pass2"),
        ]
        rotator = SeedAccountRotator(accounts)
        result = rotator.next()
        assert result.email == "valid@gmail.com"

    def test_empty_password_skipped(self):
        accounts = [
            SeedAccount(email="no_pass@gmail.com", password=""),
            SeedAccount(email="valid@gmail.com", password="pass2"),
        ]
        rotator = SeedAccountRotator(accounts)
        result = rotator.next()
        assert result.email == "valid@gmail.com"

    def test_all_invalid_raises(self):
        accounts = [
            SeedAccount(email="", password=""),
            SeedAccount(email="", password="pass"),
        ]
        rotator = SeedAccountRotator(accounts)
        with pytest.raises(NoSeedAccountError):
            rotator.next()

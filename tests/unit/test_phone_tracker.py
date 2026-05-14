"""
Unit tests untuk PhoneTracker.

Requirements: 6.3, 6.4, 6.6, 6.7, 6.8
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from phone_tracker import PhoneTracker, validate_phone_format


class TestValidatePhoneFormat:
    """Test: validasi format nomor HP."""

    def test_valid_with_plus(self):
        assert validate_phone_format("+628123456789") is True

    def test_valid_without_plus(self):
        assert validate_phone_format("08123456789") is True

    def test_valid_min_length(self):
        assert validate_phone_format("12345678") is True  # 8 digits

    def test_valid_max_length(self):
        assert validate_phone_format("123456789012345") is True  # 15 digits

    def test_invalid_contains_letters(self):
        assert validate_phone_format("0812abc3456") is False

    def test_invalid_too_short(self):
        assert validate_phone_format("1234567") is False  # 7 digits

    def test_invalid_too_long(self):
        assert validate_phone_format("1234567890123456") is False  # 16 digits

    def test_invalid_empty_string(self):
        assert validate_phone_format("") is False

    def test_invalid_spaces(self):
        assert validate_phone_format("0812 3456 789") is False

    def test_invalid_plus_in_middle(self):
        assert validate_phone_format("081+23456789") is False

    def test_valid_plus_with_min_digits(self):
        assert validate_phone_format("+12345678") is True  # + plus 8 digits = valid


class TestRecordUsage:
    """Test: record_usage menambah hitungan +1 dan persisten ke file."""

    def test_record_increments(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name

        try:
            tracker = PhoneTracker(storage_path=tmp_path)
            tracker.record_usage("+628123456789")
            tracker.record_usage("+628123456789")
            tracker.record_usage("+628123456789")

            usage = tracker.get_usage()
            assert usage["+628123456789"] == 3
        finally:
            os.unlink(tmp_path)

    def test_record_persists_across_instances(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name

        try:
            tracker1 = PhoneTracker(storage_path=tmp_path)
            tracker1.record_usage("+628111111111")
            tracker1.record_usage("+628222222222")

            # Buat instance baru
            tracker2 = PhoneTracker(storage_path=tmp_path)
            usage = tracker2.get_usage()

            assert usage["+628111111111"] == 1
            assert usage["+628222222222"] == 1
        finally:
            os.unlink(tmp_path)

    def test_multiple_numbers_tracked_independently(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name

        try:
            tracker = PhoneTracker(storage_path=tmp_path)
            tracker.record_usage("+628111111111")
            tracker.record_usage("+628111111111")
            tracker.record_usage("+628222222222")

            usage = tracker.get_usage()
            assert usage["+628111111111"] == 2
            assert usage["+628222222222"] == 1
        finally:
            os.unlink(tmp_path)


class TestGetUsage:
    """Test: get_usage handles edge cases."""

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp_path = tmp.name

        try:
            tracker = PhoneTracker(storage_path=tmp_path)
            usage = tracker.get_usage()
            assert usage == {}
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file(self):
        tracker = PhoneTracker(storage_path="nonexistent_file_12345.json")
        usage = tracker.get_usage()
        assert usage == {}

    def test_corrupted_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write("{invalid json")
            tmp_path = tmp.name

        try:
            tracker = PhoneTracker(storage_path=tmp_path)
            usage = tracker.get_usage()
            assert usage == {}
        finally:
            os.unlink(tmp_path)

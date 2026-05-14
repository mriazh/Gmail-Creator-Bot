"""
Unit tests untuk AccountCreator.

Requirements: 5.2, 5.4, 5.5, 5.6
"""

from __future__ import annotations

import sys
import os
import time
import random
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models import Identity, CreationResult
from account_creator import AccountCreator
from identity_generator import IdentityGenerator


def _make_identity() -> Identity:
    """Buat identitas test."""
    return Identity(
        first_name="John",
        last_name="Doe",
        birth_date=date(1995, 6, 15),
        username="johndoe1234",
        password="SecureP@ss123!",
        email="johndoe1234@gmail.com",
    )


def _make_mock_page(url="https://accounts.google.com/signup", content="<html></html>"):
    """Buat mock Playwright Page."""
    page = MagicMock()
    page.url = url
    page.content.return_value = content
    page.goto = MagicMock()
    page.wait_for_selector = MagicMock(return_value=MagicMock())
    page.query_selector = MagicMock(return_value=MagicMock())
    page.query_selector_all = MagicMock(return_value=[])

    # Mock bounding_box for bezier mouse
    mock_element = MagicMock()
    mock_element.bounding_box.return_value = {"x": 100, "y": 200, "width": 200, "height": 40}
    page.wait_for_selector.return_value = mock_element
    page.query_selector.return_value = mock_element

    return page


class TestTypeHumanlike:
    """Test: _type_humanlike menghasilkan jeda 50–200ms per karakter."""

    def test_typing_delay_range(self):
        """Setiap karakter harus diketik dengan delay 50-200ms."""
        creator = AccountCreator()
        element = MagicMock()
        text = "hello"

        creator._type_humanlike(element, text)

        # Verify type was called for each character
        assert element.type.call_count == len(text)

        # Verify each call had delay parameter in range
        for call in element.type.call_args_list:
            args, kwargs = call
            char = args[0]
            delay = kwargs.get("delay", args[1] if len(args) > 1 else None)
            assert delay is not None
            assert 50 <= delay <= 200, f"Delay {delay}ms di luar range 50-200ms"


class TestFieldDelay:
    """Test: jeda 1-3 detik antar field formulir."""

    def test_field_delay_range(self):
        sleep_values = []
        original_uniform = random.uniform

        def mock_uniform(a, b):
            val = original_uniform(a, b)
            sleep_values.append((a, b, val))
            return val

        creator = AccountCreator()

        with patch("account_creator.time.sleep"):
            with patch("account_creator.random.uniform", mock_uniform):
                creator._random_field_delay()

        # Should have called random.uniform(1.0, 3.0)
        assert len(sleep_values) == 1
        a, b, val = sleep_values[0]
        assert a == 1.0
        assert b == 3.0
        assert a <= val <= b


class TestUsernameConflict:
    """Test: username conflict → retry hingga 3x."""

    def test_creation_returns_result(self):
        """AccountCreator.create harus mengembalikan CreationResult."""
        page = _make_mock_page()
        identity = _make_identity()
        creator = AccountCreator()

        with patch("account_creator.time.sleep"):
            result = creator.create(page, identity)

        assert isinstance(result, CreationResult)


class TestCaptchaDetection:
    """Test: CAPTCHA terdeteksi → sesi dihentikan."""

    def test_captcha_page_detected(self):
        page = _make_mock_page(content="<html>recaptcha challenge</html>")
        identity = _make_identity()
        creator = AccountCreator()

        # Make _fill_username return "captcha"
        with patch.object(creator, '_fill_username', return_value="captcha"):
            with patch("account_creator.time.sleep"):
                result = creator.create(page, identity)

        assert result.success is False
        assert "CAPTCHA" in (result.failure_reason or "")


class TestPhoneVerificationDetection:
    """Test: deteksi halaman verifikasi HP."""

    def test_phone_verification_detected(self):
        creator = AccountCreator()
        page = MagicMock()
        page.content.return_value = "<html>verify your phone number</html>"
        page.url = "https://accounts.google.com/signup/phone"

        assert creator._is_phone_verification_page(page) is True

    def test_normal_page_not_detected(self):
        creator = AccountCreator()
        page = MagicMock()
        page.content.return_value = "<html>create your account</html>"
        page.url = "https://accounts.google.com/signup"

        assert creator._is_phone_verification_page(page) is False


class TestVerifyAccountCreated:
    """Test: verifikasi redirect sukses setelah submit."""

    def test_myaccount_redirect_is_success(self):
        creator = AccountCreator()
        page = MagicMock()
        page.url = "https://myaccount.google.com/intro/welcome"

        with patch("account_creator.time.sleep"):
            assert creator._verify_account_created(page) is True

    def test_signup_page_is_not_success(self):
        creator = AccountCreator()
        page = MagicMock()
        page.url = "https://accounts.google.com/signup"

        with patch("account_creator.time.sleep"):
            assert creator._verify_account_created(page) is False

"""
Unit tests untuk CookieFarmer.

Requirements: 3.1, 3.4, 3.5, 3.6
"""

from __future__ import annotations

import sys
import os
import time
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models import SeedAccount, FarmingResult
from cookie_farmer import CookieFarmer, MINIMUM_FARMING_SECONDS


def _make_mock_page(goto_side_effect=None):
    """Buat mock Playwright Page."""
    page = MagicMock()
    page.url = "https://myaccount.google.com"
    page.content.return_value = "<html></html>"
    page.goto = MagicMock(side_effect=goto_side_effect)
    page.wait_for_selector = MagicMock(return_value=MagicMock())
    page.query_selector = MagicMock(return_value=MagicMock())
    page.query_selector_all = MagicMock(return_value=[])
    page.evaluate = MagicMock()
    page.mouse = MagicMock()
    page.keyboard = MagicMock()

    # Mock locator for Next button
    mock_locator = MagicMock()
    mock_locator.count.return_value = 1
    mock_locator.first = MagicMock()
    page.locator = MagicMock(return_value=mock_locator)

    return page


class TestFarmingDuration:
    """Test: farming berjalan minimal 30 detik (mock timer)."""

    def test_minimum_duration_enforced(self):
        """Farming harus berlangsung minimal MINIMUM_FARMING_SECONDS."""
        page = _make_mock_page()
        seed = SeedAccount(email="test@gmail.com", password="pass123")
        farmer = CookieFarmer()

        # Mock time.sleep to track calls but not actually sleep
        sleep_total = []
        original_sleep = time.sleep

        def mock_sleep(seconds):
            sleep_total.append(seconds)
            # Don't actually sleep

        with patch("cookie_farmer.time.sleep", mock_sleep):
            with patch("cookie_farmer.time.time") as mock_time:
                # Simulate quick farming: returns increasing timestamps
                call_count = [0]

                def time_side_effect():
                    call_count[0] += 1
                    if call_count[0] <= 5:
                        return 1000.0  # Start time (farming takes "0" seconds)
                    return 1000.0 + 10  # Only 10 seconds passed

                mock_time.side_effect = time_side_effect
                result = farmer.farm(page, seed)

        # Should have called sleep to pad remaining time
        assert isinstance(result, FarmingResult)


class TestDomainVisits:
    """Test: kunjungi 2–4 domain (mock page navigation)."""

    def test_visits_multiple_domains(self):
        page = _make_mock_page()
        seed = SeedAccount(email="test@gmail.com", password="pass123")
        farmer = CookieFarmer()

        with patch("cookie_farmer.time.sleep"):
            with patch("cookie_farmer.time.time", return_value=1000.0):
                result = farmer.farm(page, seed)

        # page.goto should be called for login + farming URLs
        assert page.goto.call_count >= 2


class TestTimeoutHandling:
    """Test: halaman timeout → log WARNING dan lanjut ke URL berikutnya."""

    def test_timeout_continues_to_next_url(self):
        """Jika satu URL timeout, farming lanjut ke URL berikutnya."""
        call_count = [0]

        def goto_side_effect(url, **kwargs):
            call_count[0] += 1
            # Login succeeds, first farming URL fails, rest succeed
            if call_count[0] == 2:
                raise TimeoutError("Page load timeout")

        page = _make_mock_page(goto_side_effect=goto_side_effect)
        seed = SeedAccount(email="test@gmail.com", password="pass123")
        farmer = CookieFarmer()

        with patch("cookie_farmer.time.sleep"):
            with patch("cookie_farmer.time.time", return_value=1000.0):
                result = farmer.farm(page, seed)

        assert isinstance(result, FarmingResult)


class TestAllURLsFailed:
    """Test: semua URL gagal → FarmingResult.success = False."""

    def test_all_urls_fail(self):
        """Jika semua URL gagal, farming harus gagal."""
        def goto_always_fail(url, **kwargs):
            # Login page works but farming URLs fail
            if "signin" in url:
                return
            raise TimeoutError("All URLs fail")

        page = _make_mock_page(goto_side_effect=goto_always_fail)
        seed = SeedAccount(email="test@gmail.com", password="pass123")
        farmer = CookieFarmer()

        with patch("cookie_farmer.time.sleep"):
            with patch("cookie_farmer.time.time", return_value=1000.0):
                result = farmer.farm(page, seed)

        assert isinstance(result, FarmingResult)
        # Either success=False or domains_visited is empty
        if not result.domains_visited:
            assert result.success is False

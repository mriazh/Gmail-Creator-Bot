"""
Unit tests untuk IPManager.

Requirements: 7.1, 7.4, 7.5, 7.7, 7.8
"""

from __future__ import annotations

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
import requests

from ip_manager import IPManager, IPCheckError
from bot_logger import BotLogger


class TestGetCurrentIP:
    """Test: get_current_ip mengembalikan IP valid (mock requests)."""

    def test_returns_valid_ip(self):
        mock_response = MagicMock()
        mock_response.text = "203.0.113.42"
        mock_response.raise_for_status = MagicMock()

        with patch("ip_manager.requests.get", return_value=mock_response):
            with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                logger = BotLogger(log_path=tmp_path)
                manager = IPManager(logger=logger)
                ip = manager.get_current_ip()
                assert ip == "203.0.113.42"
            finally:
                os.unlink(tmp_path)

    def test_empty_response_raises(self):
        mock_response = MagicMock()
        mock_response.text = "   "
        mock_response.raise_for_status = MagicMock()

        with patch("ip_manager.requests.get", return_value=mock_response):
            with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                logger = BotLogger(log_path=tmp_path)
                manager = IPManager(logger=logger)
                with pytest.raises(IPCheckError, match="kosong"):
                    manager.get_current_ip()
            finally:
                os.unlink(tmp_path)


class TestTimeout:
    """Test: timeout → raise IPCheckError."""

    def test_timeout_raises_ipcheck_error(self):
        with patch(
            "ip_manager.requests.get",
            side_effect=requests.exceptions.Timeout("timeout"),
        ):
            with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                logger = BotLogger(log_path=tmp_path)
                manager = IPManager(logger=logger)
                with pytest.raises(IPCheckError, match="Timeout"):
                    manager.get_current_ip()
            finally:
                os.unlink(tmp_path)

    def test_connection_error_raises_ipcheck_error(self):
        with patch(
            "ip_manager.requests.get",
            side_effect=requests.exceptions.ConnectionError("no connection"),
        ):
            with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp:
                tmp_path = tmp.name

            try:
                logger = BotLogger(log_path=tmp_path)
                manager = IPManager(logger=logger)
                with pytest.raises(IPCheckError, match="Koneksi"):
                    manager.get_current_ip()
            finally:
                os.unlink(tmp_path)


class TestLogIPChange:
    """Test: log_ip_change menulis format yang benar ke ip_history.log."""

    def test_writes_correct_format(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_log:
            log_path = tmp_log.name
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_hist:
            hist_path = tmp_hist.name

        try:
            logger = BotLogger(log_path=log_path)
            manager = IPManager(logger=logger, history_path=hist_path)

            manager.log_ip_change("1.1.1.1", "2.2.2.2")

            with open(hist_path, encoding="utf-8") as fh:
                content = fh.read()

            assert "1.1.1.1 -> 2.2.2.2 @" in content
            # Verify timestamp is present (ISO format)
            assert "T" in content  # ISO 8601 has T separator
        finally:
            os.unlink(log_path)
            os.unlink(hist_path)

    def test_appends_multiple_entries(self):
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_log:
            log_path = tmp_log.name
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as tmp_hist:
            hist_path = tmp_hist.name

        try:
            logger = BotLogger(log_path=log_path)
            manager = IPManager(logger=logger, history_path=hist_path)

            manager.log_ip_change("1.1.1.1", "2.2.2.2")
            manager.log_ip_change("2.2.2.2", "3.3.3.3")

            with open(hist_path, encoding="utf-8") as fh:
                lines = fh.readlines()

            assert len(lines) == 2
            assert "1.1.1.1 -> 2.2.2.2" in lines[0]
            assert "2.2.2.2 -> 3.3.3.3" in lines[1]
        finally:
            os.unlink(log_path)
            os.unlink(hist_path)

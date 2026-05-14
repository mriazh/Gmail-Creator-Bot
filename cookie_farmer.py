"""
CookieFarmer — komponen Cookie Farming (Pemanasan) untuk Gmail Creator Bot.

Melakukan login seed account dan aktivitas browsing ke domain Google
untuk membangun cookie yang terlihat sah sebelum pembuatan akun baru.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

from __future__ import annotations

import logging
import math
import random
import time
from typing import Optional

from models import SeedAccount, FarmingResult

logger = logging.getLogger(__name__)

# Domain Google yang akan dikunjungi selama farming
FARMING_URLS = [
    "https://www.youtube.com",
    "https://www.google.com",
    "https://news.google.com",
    "https://www.google.com/maps",
]


MINIMUM_FARMING_SECONDS = 30
PAGE_TIMEOUT_MS = 30000  # 30 detik dalam milidetik


class CookieFarmer:
    """Melakukan login seed account dan aktivitas pemanasan browser.

    Mengunjungi 2–4 domain Google, mensimulasi interaksi manusia
    (mouse bezier, scroll, klik), dan menghabiskan minimal 30 detik
    untuk membangun cookie yang sah.

    Requirements: 3.1–3.7
    """

    def __init__(self, bot_logger=None) -> None:
        self._bot_logger = bot_logger

    def farm(self, page, seed: SeedAccount) -> FarmingResult:
        """Login seed account, kunjungi domain Google, simulasi aktivitas manusia.

        Args:
            page: Instance Playwright Page dari Camoufox.
            seed: Seed account yang akan di-login.

        Returns:
            FarmingResult dengan status keberhasilan farming.
        """
        start_time = time.time()
        domains_visited: list[str] = []
        urls_failed = 0

        try:
            # --- STEP 1: Login seed account ke Google ---
            self._log_info(f"🔑 Login seed account: {seed.email}")
            login_success = self._login_google(page, seed)
            if not login_success:
                return FarmingResult(
                    success=False,
                    domains_visited=domains_visited,
                    total_duration_seconds=time.time() - start_time,
                    error_message=f"Login seed account gagal: {seed.email}",
                )

            elapsed = time.time() - start_time
            self._log_info(f"✅ Login berhasil ({elapsed:.0f}s)")

            # --- STEP 2: Kunjungi 2–4 domain Google ---
            num_domains = random.randint(2, 4)
            selected_urls = random.sample(FARMING_URLS, min(num_domains, len(FARMING_URLS)))
            self._log_info(f"🌐 Akan mengunjungi {len(selected_urls)} domain Google...")

            for idx, url in enumerate(selected_urls, 1):
                try:
                    elapsed = time.time() - start_time
                    self._log_info(f"   [{idx}/{len(selected_urls)}] Membuka: {url} ({elapsed:.0f}s)")
                    page.goto(url, timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
                    self._random_delay(2.0, 5.0, label=f"browsing {url.split('/')[2]}")

                    # Minimal 2 aksi interaksi per domain (Requirement 3.7)
                    self._log_info(f"   [{idx}/{len(selected_urls)}] Interaksi (scroll/klik)...")
                    self._perform_interactions(page, url)

                    domains_visited.append(url)
                    elapsed = time.time() - start_time
                    self._log_info(f"   [{idx}/{len(selected_urls)}] ✅ Selesai ({elapsed:.0f}s total)")

                except Exception as exc:
                    # Requirement 3.5: timeout → log WARNING, lanjut URL berikutnya
                    urls_failed += 1
                    self._log_warning(f"   [{idx}/{len(selected_urls)}] ⚠ Gagal: {exc}")
                    continue

            # Requirement 3.6: jika semua URL gagal → error
            if not domains_visited:
                return FarmingResult(
                    success=False,
                    domains_visited=domains_visited,
                    total_duration_seconds=time.time() - start_time,
                    error_message="Semua URL farming gagal dimuat",
                )

            # --- STEP 3: Pastikan minimal 30 detik total (Requirement 3.4) ---
            elapsed = time.time() - start_time
            if elapsed < MINIMUM_FARMING_SECONDS:
                remaining = MINIMUM_FARMING_SECONDS - elapsed
                self._log_info(f"⏳ Farming baru {elapsed:.0f}s, padding {remaining:.0f}s lagi...")
                for r in range(int(remaining), 0, -1):
                    print(f"\r   ⏳ Padding: {r}s tersisa...  ", end="", flush=True)
                    time.sleep(1)
                print(f"\r   ⏳ Padding selesai.                    ")

            total_duration = time.time() - start_time
            self._log_info(
                f"🏁 Cookie farming selesai: {len(domains_visited)} domain, "
                f"{total_duration:.0f}s total"
            )

            return FarmingResult(
                success=True,
                domains_visited=domains_visited,
                total_duration_seconds=total_duration,
            )

        except Exception as exc:
            return FarmingResult(
                success=False,
                domains_visited=domains_visited,
                total_duration_seconds=time.time() - start_time,
                error_message=f"Exception di CookieFarmer: {exc}",
            )

    def _login_google(self, page, seed: SeedAccount) -> bool:
        """Login ke Google Accounts menggunakan seed account.

        Returns:
            True jika login berhasil, False jika gagal.
        """
        try:
            self._log_info("🌐 Membuka halaman login Google...")
            page.goto(
                "https://accounts.google.com/signin",
                timeout=PAGE_TIMEOUT_MS,
                wait_until="domcontentloaded",
            )
            # Tunggu halaman benar-benar selesai loading
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass  # Lanjut meski networkidle timeout
            self._random_delay(2.0, 4.0)

            # Masukkan email
            email_field = page.wait_for_selector(
                'input[type="email"]', timeout=10000
            )
            if email_field:
                self._simulate_mouse_bezier(page, email_field)
                self._type_humanlike(email_field, seed.email)
                self._random_delay(1.0, 2.0)

                # Klik Next
                next_btn = page.locator('button:has-text("Next"), #identifierNext')
                if next_btn.count() > 0:
                    next_btn.first.click()
                    self._random_delay(2.0, 4.0)

            # Masukkan password
            password_field = page.wait_for_selector(
                'input[type="password"]', timeout=10000
            )
            if password_field:
                self._simulate_mouse_bezier(page, password_field)
                self._type_humanlike(password_field, seed.password)
                self._random_delay(1.0, 2.0)

                # Klik Next
                next_btn = page.locator('button:has-text("Next"), #passwordNext')
                if next_btn.count() > 0:
                    next_btn.first.click()
                    self._random_delay(3.0, 6.0)

            # Verifikasi login berhasil
            current_url = page.url
            if "myaccount" in current_url or "accounts.google.com" in current_url:
                return True

            # Cek apakah ada halaman verifikasi tambahan
            if "challenge" in current_url or "signin" in current_url:
                self._log_warning("Google meminta verifikasi tambahan untuk seed account")
                return False

            return True

        except Exception as exc:
            self._log_warning(f"Exception saat login: {exc}")
            return False

    def _perform_interactions(self, page, url: str) -> None:
        """Lakukan minimal 2 aksi interaksi per domain.

        Requirement 3.7: minimal 2 aksi (klik atau scroll) per domain.
        Semua aksi dibungkus try/except agar tidak hang.
        """
        actions_done = 0

        # Aksi 1: Scroll ke bawah
        try:
            scroll_amount = random.randint(200, 600)
            print(f"      ↕ Scroll {scroll_amount}px...", flush=True)
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            self._random_delay(1.0, 3.0)
            actions_done += 1
        except Exception:
            pass

        # Aksi 2: Interaksi spesifik domain (simplified, no typing)
        try:
            if "youtube.com" in url:
                self._youtube_interaction(page)
            elif "google.com" in url and "maps" not in url and "news" not in url:
                self._google_search_interaction(page)
            else:
                # Maps/News: scroll lagi aja
                scroll_amount = random.randint(100, 400)
                print(f"      ↕ Scroll lagi {scroll_amount}px...", flush=True)
                page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                self._random_delay(1.0, 2.0)
            actions_done += 1
        except Exception as exc:
            print(f"      ⚠ Interaksi gagal (minor): {str(exc)[:80]}", flush=True)
            actions_done += 1  # Count anyway, jangan loop forever

        # Jika masih kurang 2 aksi, scroll lagi
        while actions_done < 2:
            try:
                page.evaluate(f"window.scrollBy(0, {random.randint(100, 300)})")
                self._random_delay(1.0, 2.0)
                actions_done += 1
            except Exception:
                actions_done += 1  # Force break

    def _youtube_interaction(self, page) -> None:
        """Interaksi YouTube: scroll dan coba klik thumbnail."""
        print("      🎬 YouTube: scrolling...", flush=True)

        # Scroll ke bawah untuk lihat video
        page.evaluate("window.scrollBy(0, 500)")
        self._random_delay(2.0, 4.0)

        # Coba klik thumbnail video (simple, no search)
        try:
            print("      🎬 YouTube: mencari video thumbnail...", flush=True)
            thumbnail = page.query_selector(
                'a#thumbnail, ytd-thumbnail a, a[href*="watch"]'
            )
            if thumbnail:
                thumbnail.click(timeout=5000)
                print("      🎬 YouTube: menonton video...", flush=True)
                self._random_delay(4.0, 8.0)  # Tonton sebentar
            else:
                print("      🎬 YouTube: no thumbnails found, scrolling more...", flush=True)
                page.evaluate("window.scrollBy(0, 400)")
                self._random_delay(2.0, 3.0)
        except Exception as exc:
            print(f"      🎬 YouTube: klik gagal (minor): {str(exc)[:60]}", flush=True)

    def _google_search_interaction(self, page) -> None:
        """Interaksi Google Search: scroll halaman dan baca hasil."""
        print("      🔍 Google: scrolling results...", flush=True)

        # Scroll halaman beberapa kali (simulasi baca hasil)
        for i in range(random.randint(2, 3)):
            page.evaluate(f"window.scrollBy(0, {random.randint(200, 500)})")
            self._random_delay(1.5, 3.0)

        # Coba klik link hasil pencarian
        try:
            print("      🔍 Google: mencari link...", flush=True)
            links = page.query_selector_all('a[href*="http"]:not([href*="google"])')
            if links and len(links) > 2:
                target = links[random.randint(0, min(4, len(links) - 1))]
                target.click(timeout=5000)
                print("      🔍 Google: membuka link...", flush=True)
                self._random_delay(3.0, 5.0)
                page.go_back(timeout=10000)
            else:
                page.evaluate("window.scrollBy(0, 300)")
        except Exception as exc:
            print(f"      🔍 Google: klik gagal (minor): {str(exc)[:60]}", flush=True)
            self._log_warning(f"Google Search interaction gagal: {exc}")

    def _simulate_mouse_bezier(self, page, target) -> None:
        """Gerakkan mouse menggunakan kurva bezier ke target elemen.

        Requirement 3.3: minimal 3 gerakan mouse non-linear sebelum klik.
        """
        try:
            box = target.bounding_box()
            if not box:
                return

            # Target coordinates (center of element)
            target_x = box["x"] + box["width"] / 2
            target_y = box["y"] + box["height"] / 2

            # Current mouse position (random starting point)
            current_x = random.randint(100, 800)
            current_y = random.randint(100, 500)

            # Generate 3+ bezier curve points
            num_steps = random.randint(3, 6)
            for i in range(num_steps):
                t = (i + 1) / num_steps

                # Bezier control points with randomness
                ctrl_x = current_x + random.randint(-50, 50)
                ctrl_y = current_y + random.randint(-30, 30)

                # Quadratic bezier interpolation
                x = (1 - t) ** 2 * current_x + 2 * (1 - t) * t * ctrl_x + t ** 2 * target_x
                y = (1 - t) ** 2 * current_y + 2 * (1 - t) * t * ctrl_y + t ** 2 * target_y

                page.mouse.move(x, y)
                time.sleep(random.uniform(0.05, 0.15))

        except Exception:
            # If bezier fails, just move directly
            pass

    def _type_humanlike(self, element, text: str) -> None:
        """Ketik teks karakter per karakter dengan jeda acak.

        Requirement 3.2: jeda acak antara 50-200ms per karakter.
        """
        for char in text:
            element.type(char, delay=random.randint(50, 200))

    def _random_delay(self, min_s: float = 2.0, max_s: float = 8.0, label: str = "") -> None:
        """Jeda acak antara aksi (Requirement 3.2)."""
        delay = random.uniform(min_s, max_s)
        if delay >= 2.0:
            desc = f" ({label})" if label else ""
            for r in range(int(delay), 0, -1):
                print(f"\r   ⏱ Jeda{desc}: {r}s...  ", end="", flush=True)
                time.sleep(1)
            # Sisa waktu sub-detik
            time.sleep(delay - int(delay))
            print(f"\r   ⏱ Jeda{desc}: done.       ", flush=True)
        else:
            time.sleep(delay)

    def _log_info(self, message: str) -> None:
        print(f"   {message}")
        logger.info(message)
        if self._bot_logger:
            self._bot_logger.info("CookieFarmer", message)

    def _log_warning(self, message: str) -> None:
        print(f"   {message}")
        logger.warning(message)
        if self._bot_logger:
            self._bot_logger.warning("CookieFarmer", message)

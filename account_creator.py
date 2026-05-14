"""
AccountCreator — pembuatan akun Gmail berdasarkan flow Google terbaru.

Flow (dari screenshot real):
1. Nama depan + belakang → Berikutnya
2. Hari/Bulan/Tahun + Gender → Berikutnya
3. (Gmail address suggestion/skip)
4. Sandi + Konfirmasi → Berikutnya
5. QR Code verifikasi ponsel → user scan manual
6. Jika nomor sudah terpakai → coba nomor lain

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

from models import Identity, CreationResult
from identity_generator import IdentityGenerator

logger = logging.getLogger(__name__)

SIGNUP_URL = "https://accounts.google.com/lifecycle/steps/signup/name"
PAGE_TIMEOUT_MS = 30000
QR_SCAN_TIMEOUT = 300  # 5 menit menunggu user scan QR


class AccountCreator:
    """Mengisi formulir pendaftaran Gmail sesuai flow Google terbaru."""

    def __init__(self, identity_generator=None, bot_logger=None):
        self._identity_gen = identity_generator or IdentityGenerator()
        self._bot_logger = bot_logger

    def create(self, page, identity: Identity) -> CreationResult:
        """Jalankan flow signup lengkap."""
        try:
            # === STEP 1: Buka halaman & isi Nama ===
            self._log_info("Membuka halaman pendaftaran Gmail...")
            page.goto(SIGNUP_URL, timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")
            self._wait_page_ready(page)
            self._random_field_delay()

            self._log_info(f"Mengisi nama: {identity.first_name} {identity.last_name}")
            self._fill_name(page, identity)
            self._click_next(page)
            self._random_field_delay()
            self._wait_page_ready(page)

            # === STEP 2: Isi Tanggal Lahir & Gender ===
            self._log_info(f"Mengisi tanggal lahir: {identity.birth_date}")
            if "birthdaygender" in page.url or "birthday" in page.url:
                self._fill_birthday_gender(page, identity)
                self._click_next(page)
                self._random_field_delay()
                self._wait_page_ready(page)
            else:
                self._log_warning(f"Halaman birthday tidak terdeteksi. URL: {page.url}")

            # === STEP 3: Gmail address (jika muncul) ===
            if "choosegmailaddress" in page.url or "username" in page.url:
                self._log_info("Halaman pilih Gmail address terdeteksi")
                self._fill_gmail_address(page, identity)
                self._click_next(page)
                self._random_field_delay()
                self._wait_page_ready(page)

            # === STEP 4: Isi Password ===
            if "password" in page.url:
                self._log_info("Mengisi password...")
                self._fill_password(page, identity.password)
                self._click_next(page)
                self._random_field_delay()
                self._wait_page_ready(page)
            else:
                self._log_warning(f"Halaman password tidak terdeteksi. URL: {page.url}")

            # === STEP 5: Recovery phone/email (jika muncul, skip) ===
            if "recovery" in page.url or "phonenumber" in page.url:
                self._log_info("Halaman recovery — mencoba skip...")
                self._click_skip_or_next(page)
                self._random_field_delay()
                self._wait_page_ready(page)

            # === STEP 6: QR Code / Phone Verification ===
            if "mophoneverification" in page.url or "phoneverification" in page.url:
                self._log_info("🔲 QR Code verifikasi terdeteksi!")
                return self._handle_qr_verification(page, identity)

            # === STEP 7: Challenge / verifikasi lain ===
            if "challenge" in page.url:
                self._log_warning("Google meminta verifikasi tambahan!")
                return CreationResult(
                    success=False,
                    email=identity.email,
                    failure_reason="Challenge/verifikasi tambahan diperlukan",
                )

            # === STEP 8: Terms of Service ===
            if "terms" in page.url or "tos" in page.url:
                self._log_info("Menyetujui Terms of Service...")
                self._click_agree(page)
                self._random_field_delay()
                self._wait_page_ready(page)

            # === STEP 9: Cek sukses ===
            if self._is_success_page(page):
                email = self._extract_email(page) or identity.email
                self._log_info(f"✅ Akun berhasil dibuat: {email}")
                return CreationResult(success=True, email=email)

            # Belum sukses — cek URL untuk info
            self._log_warning(f"Status tidak diketahui. URL: {page.url}")
            return CreationResult(
                success=False,
                email=identity.email,
                failure_reason=f"Status tidak diketahui. URL akhir: {page.url}",
            )

        except Exception as exc:
            self._log_error(f"Exception: {exc}")
            return CreationResult(success=False, failure_reason=f"Exception: {exc}")

    # ---------------------------------------------------------------
    # Form Fillers
    # ---------------------------------------------------------------

    def _fill_name(self, page, identity: Identity):
        """Isi Nama depan & belakang."""
        # Coba selector berdasarkan name attribute (language-independent)
        first = page.query_selector('input[name="firstName"]')
        if not first:
            # Fallback: cari semua input text, ambil yang pertama
            inputs = page.query_selector_all('input[type="text"], input:not([type])')
            first = inputs[0] if inputs else None

        if first:
            self._type_humanlike(first, identity.first_name)
            self._random_field_delay()

        last = page.query_selector('input[name="lastName"]')
        if not last:
            inputs = page.query_selector_all('input[type="text"], input:not([type])')
            last = inputs[1] if len(inputs) > 1 else None

        if last:
            self._type_humanlike(last, identity.last_name)

    def _fill_birthday_gender(self, page, identity: Identity):
        """Isi Hari, Bulan, Tahun, Gender.

        Format dari SS: Hari (input) | Bulan (dropdown) | Tahun (input) | Gender (dropdown)
        """
        # Hari (Day)
        day_field = page.query_selector('input[name="day"], input#day')
        if not day_field:
            # Fallback: input pertama di halaman
            inputs = page.query_selector_all('input[type="text"], input:not([type])')
            day_field = inputs[0] if inputs else None
        if day_field:
            self._type_humanlike(day_field, str(identity.birth_date.day))
            self._random_field_delay()

        # Bulan (Month) — dropdown/select
        month_select = page.query_selector('select#month, select[name="month"]')
        if not month_select:
            selects = page.query_selector_all('select')
            month_select = selects[0] if selects else None
        if month_select:
            month_select.select_option(str(identity.birth_date.month))
            self._random_field_delay()

        # Tahun (Year)
        year_field = page.query_selector('input[name="year"], input#year')
        if not year_field:
            inputs = page.query_selector_all('input[type="text"], input:not([type])')
            year_field = inputs[1] if len(inputs) > 1 else None
        if year_field:
            self._type_humanlike(year_field, str(identity.birth_date.year))
            self._random_field_delay()

        # Gender — dropdown/select
        gender_select = page.query_selector('select#gender, select[name="gender"]')
        if not gender_select:
            selects = page.query_selector_all('select')
            gender_select = selects[-1] if selects else None
        if gender_select:
            gender_val = random.choice(["1", "2"])  # 1=Male, 2=Female
            gender_select.select_option(gender_val)

    def _fill_gmail_address(self, page, identity: Identity):
        """Isi/pilih Gmail address jika step ini muncul."""
        # Coba klik "Buat alamat Gmail Anda sendiri" jika ada
        custom = page.query_selector('div[data-value="custom"], [data-action="custom"]')
        if custom:
            custom.click()
            self._random_field_delay()

        username_field = page.query_selector(
            'input[name="Username"], input[name="username"], input[type="text"]'
        )
        if username_field:
            username_field.fill("")
            self._type_humanlike(username_field, identity.username)

    def _fill_password(self, page, password: str):
        """Isi Sandi dan Konfirmasi."""
        pw_fields = page.query_selector_all('input[type="password"]')
        if len(pw_fields) >= 2:
            self._type_humanlike(pw_fields[0], password)
            self._random_field_delay()
            self._type_humanlike(pw_fields[1], password)
        elif len(pw_fields) == 1:
            self._type_humanlike(pw_fields[0], password)
            # Cari confirm terpisah
            confirm = page.query_selector('input[name="ConfirmPasswd"]')
            if confirm:
                self._random_field_delay()
                self._type_humanlike(confirm, password)

    # ---------------------------------------------------------------
    # QR Code Verification Handler
    # ---------------------------------------------------------------

    def _handle_qr_verification(self, page, identity: Identity) -> CreationResult:
        """Handle halaman QR code verification.

        Bot pause, user harus scan QR code secara manual.
        """
        print("\n" + "=" * 50)
        print("  📱 VERIFIKASI QR CODE DIPERLUKAN!")
        print("=" * 50)
        print("  1. Buka kamera HP Anda")
        print("  2. Scan QR code yang muncul di browser")
        print("  3. Ikuti langkah di HP untuk verifikasi")
        print("  4. Setelah selesai, browser akan otomatis lanjut")
        print()
        print(f"  ⏱  Menunggu maksimal {QR_SCAN_TIMEOUT // 60} menit...")
        print("  (Tekan Ctrl+C jika ingin skip)")
        print("=" * 50)

        start = time.time()
        while time.time() - start < QR_SCAN_TIMEOUT:
            time.sleep(3)
            current_url = page.url.lower()
            elapsed = int(time.time() - start)
            print(f"\r  ⏱  Menunggu verifikasi... {elapsed}s  ", end="", flush=True)

            # Cek apakah sudah pindah dari halaman verifikasi
            if "mophoneverification" not in current_url and "phoneverification" not in current_url:
                print()

                # Cek error: nomor sudah terlalu sering digunakan
                if "error" in current_url:
                    page_text = page.content().lower()
                    if "terlalu sering" in page_text or "too often" in page_text:
                        self._log_warning("Nomor telepon sudah terlalu sering digunakan!")
                        print("\n  ⚠  Nomor telepon sudah terlalu sering digunakan!")
                        print("  Klik 'Berikutnya' di browser untuk coba nomor lain,")
                        print("  atau tekan Enter untuk lanjut...")
                        input("  > ")
                        continue

                # Cek sukses
                if self._is_success_page(page):
                    email = self._extract_email(page) or identity.email
                    self._log_info(f"✅ Verifikasi berhasil! Akun: {email}")
                    return CreationResult(success=True, email=email)

                # Mungkin ada step lanjutan (TOS, username, dll)
                self._log_info(f"Halaman berubah ke: {page.url}")
                self._handle_post_verification(page)

                if self._is_success_page(page):
                    email = self._extract_email(page) or identity.email
                    return CreationResult(success=True, email=email)

                return CreationResult(
                    success=False,
                    email=identity.email,
                    failure_reason=f"Post-verification URL: {page.url}",
                )

        print()
        self._log_warning("Timeout menunggu QR verification")
        return CreationResult(
            success=False,
            email=identity.email,
            failure_reason="QR verification timeout",
        )

    def _handle_post_verification(self, page):
        """Handle steps setelah QR verification (TOS, username, recovery, dll)."""
        for _ in range(5):  # Max 5 steps
            time.sleep(2)
            url = page.url.lower()

            if self._is_success_page(page):
                return

            if "terms" in url or "tos" in url or "consent" in url:
                self._log_info("Menyetujui Terms of Service...")
                self._click_agree(page)
                self._random_field_delay()
            elif "recovery" in url:
                self._log_info("Skip recovery...")
                self._click_skip_or_next(page)
                self._random_field_delay()
            elif "username" in url or "choosegmail" in url:
                self._log_info("Username step — skipping (auto-assigned)...")
                self._click_next(page)
                self._random_field_delay()
            else:
                self._click_next(page)
                self._random_field_delay()

    # ---------------------------------------------------------------
    # Navigation Helpers
    # ---------------------------------------------------------------

    def _click_next(self, page):
        """Klik Berikutnya / Next."""
        selectors = [
            'button:has-text("Berikutnya")',
            'button:has-text("Next")',
            'button:has-text("Lanjutkan")',
            '#identifierNext',
            '#passwordNext',
            'button[type="submit"]',
            'div[role="button"]:has-text("Berikutnya")',
            'div[role="button"]:has-text("Next")',
        ]
        for sel in selectors:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click(timeout=5000)
                    return
            except Exception:
                continue

    def _click_skip_or_next(self, page):
        """Klik Skip / Lewati, atau Next jika skip ga ada."""
        skip_selectors = [
            'button:has-text("Lewati")',
            'button:has-text("Skip")',
            'span:has-text("Lewati")',
            'span:has-text("Skip")',
        ]
        for sel in skip_selectors:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click(timeout=5000)
                    return
            except Exception:
                continue
        self._click_next(page)

    def _click_agree(self, page):
        """Klik I agree / Saya setuju."""
        agree_selectors = [
            'button:has-text("Saya setuju")',
            'button:has-text("I agree")',
            'button:has-text("Setuju")',
            'button:has-text("Agree")',
            'button:has-text("Accept")',
        ]
        for sel in agree_selectors:
            try:
                btn = page.query_selector(sel)
                if btn:
                    btn.click(timeout=5000)
                    return
            except Exception:
                continue
        self._click_next(page)

    # ---------------------------------------------------------------
    # Detection Helpers
    # ---------------------------------------------------------------

    def _is_success_page(self, page) -> bool:
        """Cek apakah akun berhasil dibuat."""
        try:
            url = page.url.lower()
            return any(s in url for s in [
                "myaccount.google.com", "welcome", "gettingstarted",
                "setupprofile", "newaccount",
            ])
        except Exception:
            return False

    def _extract_email(self, page) -> Optional[str]:
        """Coba extract email dari halaman sukses."""
        try:
            # Cari text yang mengandung @gmail.com
            text = page.content()
            import re
            match = re.search(r'[\w.]+@gmail\.com', text)
            return match.group(0) if match else None
        except Exception:
            return None

    def _wait_page_ready(self, page):
        """Tunggu halaman siap."""
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            time.sleep(2)

    # ---------------------------------------------------------------
    # Human-like Helpers
    # ---------------------------------------------------------------

    def _type_humanlike(self, element, text: str):
        """Ketik per karakter, 50-200ms delay. (Req 5.2)"""
        for char in text:
            element.type(char, delay=random.randint(50, 200))

    def _random_field_delay(self):
        """Jeda 1-3 detik antar field. (Req 5.3)"""
        time.sleep(random.uniform(1.0, 3.0))

    # ---------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------

    def _log_info(self, msg):
        print(f"   📝 {msg}")
        logger.info(msg)
        if self._bot_logger:
            self._bot_logger.info("AccountCreator", msg)

    def _log_warning(self, msg):
        print(f"   ⚠  {msg}")
        logger.warning(msg)
        if self._bot_logger:
            self._bot_logger.warning("AccountCreator", msg)

    def _log_error(self, msg):
        print(f"   ❌ {msg}")
        logger.error(msg)
        if self._bot_logger:
            self._bot_logger.error("AccountCreator", msg)

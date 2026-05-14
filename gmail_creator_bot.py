"""
Gmail Creator Bot — Orchestrator utama.

Menjalankan alur pembuatan akun Gmail secara batch:
1. Inisialisasi stealth browser (Camoufox)
2. Cookie farming (login seed account + browsing)
3. Pembuatan akun baru (isi formulir pendaftaran)

Mendukung:
- Rotasi seed account (round-robin)
- Rotasi IP manual (tethering)
- Verifikasi nomor HP manual
- Rate limiting antar sesi
- Graceful shutdown (Ctrl+C)

Usage:
    python gmail_creator_bot.py
"""

from __future__ import annotations

import signal
import sys
import time
from collections import Counter
from datetime import datetime
from typing import Optional

from models import BatchStats, SessionResult
from config_loader import ConfigLoader, ConfigError
from bot_logger import BotLogger
from seed_account_rotator import SeedAccountRotator, NoSeedAccountError
from identity_generator import IdentityGenerator
from credential_store import CredentialStore
from ip_manager import IPManager, IPCheckError
from phone_tracker import PhoneTracker
from rate_limiter import RateLimiter
from cookie_farmer import CookieFarmer
from account_creator import AccountCreator


class GmailCreatorBot:
    """Orchestrator utama untuk batch pembuatan akun Gmail.

    Mengelola lifecycle seluruh sesi: mulai dari inisialisasi browser,
    cookie farming, pembuatan akun, hingga penyimpanan kredensial.

    Requirements: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
    """

    def __init__(self) -> None:
        self._shutdown_requested = False
        self._current_browser = None

        # Statistik batch
        self._stats = BatchStats(
            total_sessions=0,
            successful=0,
            failed=0,
            failure_reasons=Counter(),
            start_time=datetime.now(),
        )

        # Session results
        self._results: list[SessionResult] = []

    def run(self) -> None:
        """Entry point utama bot."""
        print("=" * 60)
        print("  GMAIL CREATOR BOT — Camoufox + Cookie Farming")
        print("=" * 60)
        print()

        # --- STEP 1: Load Config ---
        try:
            loader = ConfigLoader()
            config = loader.load("config.json")
        except ConfigError as exc:
            print(f"\n❌ Error konfigurasi: {exc}")
            sys.exit(1)
        except SystemExit:
            # ConfigLoader creates default and exits
            raise

        # --- STEP 2: Initialize components ---
        logger = BotLogger()
        logger.info("Bot", "Gmail Creator Bot dimulai")

        seed_rotator = SeedAccountRotator(config.seed_accounts)
        identity_gen = IdentityGenerator(locale=config.faker_locale)
        cred_store = CredentialStore(logger=logger)
        ip_manager = IPManager(logger=logger)
        phone_tracker = PhoneTracker()
        rate_limiter = RateLimiter()
        cookie_farmer = CookieFarmer(bot_logger=logger)
        account_creator = AccountCreator(
            identity_generator=identity_gen,
            bot_logger=logger,
        )

        # --- STEP 3: Setup signal handler (Ctrl+C) ---
        # Requirement 12.5
        def handle_sigint(signum, frame):
            if self._shutdown_requested:
                # Ctrl+C kedua kali → force exit
                print("\n\n❌ Force exit!")
                self._stats.end_time = datetime.now()
                logger.summary(self._stats)
                sys.exit(1)
            print("\n\n⚠  Ctrl+C terdeteksi! Tekan Ctrl+C lagi untuk force exit.")
            self._shutdown_requested = True

        signal.signal(signal.SIGINT, handle_sigint)

        # --- STEP 4: Cek IP awal ---
        try:
            current_ip = ip_manager.get_current_ip()
            logger.info("Bot", f"IP awal: {current_ip}")
            print(f"🌐 IP awal: {current_ip}")
        except IPCheckError as exc:
            logger.error("Bot", f"Gagal mendapatkan IP awal: {exc}")
            print(f"⚠  Gagal cek IP awal: {exc}")
            confirm = input("Lanjutkan tanpa verifikasi IP? (y/n): ").strip().lower()
            if confirm != "y":
                sys.exit(1)
            current_ip = "UNKNOWN"

        print(f"\n📊 Target: {config.total_accounts} akun")
        print(f"🔄 Rotasi IP setiap: {config.accounts_per_ip_rotation} akun")
        print(f"⏱  Jeda antar sesi: {config.delay_min}-{config.delay_max} detik")
        print(f"🌱 Seed accounts: {len(config.seed_accounts)} akun")
        print(f"📱 Nomor HP: {len(config.phone_numbers)} nomor")
        print()

        # --- STEP 5: Main session loop ---
        accounts_created_since_ip_rotation = 0

        for session_num in range(1, config.total_accounts + 1):
            if self._shutdown_requested:
                logger.info("Bot", "Shutdown diminta oleh pengguna")
                break

            session_start = time.time()
            print(f"\n{'━' * 60}")
            print(f"  SESI {session_num}/{config.total_accounts}")
            print(f"{'━' * 60}")

            # Requirement 12.4: pastikan browser selalu ditutup
            browser = None
            try:
                # --- 5a: Get seed account ---
                try:
                    seed = seed_rotator.next()
                    logger.info("Bot", f"Seed account: {seed.email}")
                    print(f"🌱 Seed: {seed.email}")
                except NoSeedAccountError as exc:
                    logger.error("Bot", f"Semua seed account habis: {exc}")
                    print(f"\n❌ {exc}")
                    break

                # --- 5b: Initialize Camoufox ---
                # Requirement 1.1–1.5
                print("🔧 Menginisialisasi Camoufox...")
                try:
                    from camoufox.sync_api import Camoufox

                    browser_ctx = Camoufox(humanize=True)
                    browser = browser_ctx.__enter__()
                    page = browser.new_page()

                    # Stabilisasi: buka halaman kosong dulu, tunggu browser siap
                    page.goto("about:blank")
                    time.sleep(2)
                    print("✅ Browser stealth aktif")
                except Exception as exc:
                    logger.error("Bot", f"Gagal inisialisasi Camoufox: {exc}", exc_info=True)
                    print(f"❌ Gagal inisialisasi browser: {exc}")
                    self._record_failure(
                        session_num, seed.email, "INIT", str(exc), session_start
                    )
                    seed_rotator.mark_failed_temporary(seed.email)
                    continue

                # --- 5c: Cookie Farming ---
                # Requirement 3.1–3.7
                print("🍪 Memulai cookie farming...")
                farming_result = cookie_farmer.farm(page, seed)

                if not farming_result.success:
                    logger.warning(
                        "Bot",
                        f"Cookie farming gagal: {farming_result.error_message}",
                    )
                    print(f"⚠  Farming gagal: {farming_result.error_message}")

                    # Semua login failure → temporary dulu (bisa jadi network issue)
                    # Hanya permanent jika credential salah (bukan crash/timeout)
                    seed_rotator.mark_failed_temporary(seed.email)

                    self._record_failure(
                        session_num,
                        seed.email,
                        "COOKIE_FARMING",
                        farming_result.error_message or "Unknown",
                        session_start,
                    )
                    continue

                print(
                    f"✅ Farming selesai: {len(farming_result.domains_visited)} domain, "
                    f"{farming_result.total_duration_seconds:.0f}s"
                )

                # --- 5d: Generate identity ---
                print("🎭 Generating identitas...")
                try:
                    identity = identity_gen.generate()
                    logger.info(
                        "Bot",
                        f"Identitas: {identity.first_name} {identity.last_name} "
                        f"({identity.username})",
                    )
                    print(f"   Nama    : {identity.first_name} {identity.last_name}")
                    print(f"   Username: {identity.username}")
                except RuntimeError as exc:
                    logger.error("Bot", f"Gagal generate identitas: {exc}")
                    self._record_failure(
                        session_num, seed.email, "IDENTITY_GEN", str(exc), session_start
                    )
                    continue

                # --- 5e: Create account ---
                print("📝 Mengisi formulir pendaftaran...")
                creation_result = account_creator.create(page, identity)

                if creation_result.success:
                    # Requirement 8.1: simpan kredensial
                    cred_store.save(
                        creation_result.email or identity.email,
                        identity.password,
                        datetime.now(),
                    )
                    # Requirement 8.3: catat seed account dan IP
                    logger.info(
                        "Bot",
                        f"Akun berhasil: {creation_result.email} "
                        f"(seed={seed.email}, IP={current_ip})",
                    )
                    print(f"\n✅ BERHASIL: {creation_result.email}")

                    self._record_success(
                        session_num,
                        seed.email,
                        creation_result.email or identity.email,
                        session_start,
                    )

                    accounts_created_since_ip_rotation += 1

                elif creation_result.failure_reason == "Verifikasi HP diperlukan":
                    # --- 5f: Handle phone verification ---
                    print("\n📱 Verifikasi nomor HP diperlukan!")

                    if config.phone_numbers:
                        phone_number = phone_tracker.prompt_phone_input(
                            config.phone_numbers
                        )
                        if phone_number:
                            # Input nomor HP ke halaman Google
                            phone_field = page.query_selector('input[type="tel"]')
                            if phone_field:
                                for char in phone_number:
                                    phone_field.type(char, delay=100)
                                time.sleep(1)

                                # Klik Send/Next
                                send_btn = page.query_selector(
                                    'button:has-text("Next"), button:has-text("Send")'
                                )
                                if send_btn:
                                    send_btn.click()
                                    time.sleep(3)

                                # Minta OTP
                                print("Masukkan kode OTP yang diterima:")
                                otp = input("> ").strip()
                                if otp:
                                    otp_field = page.query_selector(
                                        'input[type="tel"], input[name="code"]'
                                    )
                                    if otp_field:
                                        otp_field.fill("")
                                        for char in otp:
                                            otp_field.type(char, delay=100)
                                        time.sleep(1)

                                        # Klik Verify
                                        verify_btn = page.query_selector(
                                            'button:has-text("Verify"), '
                                            'button:has-text("Next")'
                                        )
                                        if verify_btn:
                                            verify_btn.click()
                                            time.sleep(3)

                                        phone_tracker.record_usage(phone_number)

                                        # Cek apakah berhasil setelah OTP
                                        if "myaccount" in page.url.lower():
                                            cred_store.save(
                                                identity.email,
                                                identity.password,
                                                datetime.now(),
                                            )
                                            print(f"\n✅ BERHASIL (via OTP): {identity.email}")
                                            self._record_success(
                                                session_num,
                                                seed.email,
                                                identity.email,
                                                session_start,
                                            )
                                            accounts_created_since_ip_rotation += 1
                                            continue

                    self._record_failure(
                        session_num,
                        seed.email,
                        "VERIFICATION",
                        "Verifikasi HP gagal/dilewati",
                        session_start,
                    )

                else:
                    # Gagal karena alasan lain
                    logger.warning(
                        "Bot",
                        f"Pembuatan akun gagal: {creation_result.failure_reason}",
                    )
                    print(f"❌ Gagal: {creation_result.failure_reason}")
                    self._record_failure(
                        session_num,
                        seed.email,
                        "FORM_FILL",
                        creation_result.failure_reason or "Unknown",
                        session_start,
                    )

            except Exception as exc:
                # Requirement 12.1: tangkap exception, log, lanjut
                logger.error(
                    "Bot",
                    f"Exception tidak tertangani di sesi {session_num}: {exc}",
                    exc_info=True,
                )
                print(f"\n❌ Exception: {exc}")
                self._record_failure(
                    session_num,
                    seed.email if 'seed' in dir() else "UNKNOWN",
                    "INIT",
                    str(exc),
                    session_start,
                )

            finally:
                # Requirement 12.4: selalu tutup browser
                if browser is not None:
                    try:
                        browser_ctx.__exit__(None, None, None)
                        print("🔒 Browser ditutup")
                    except Exception:
                        pass

            # --- STEP 6: Rate limiting ---
            if not self._shutdown_requested and session_num < config.total_accounts:
                print(f"\n⏱  Menunggu sebelum sesi berikutnya...")
                rate_limiter.wait_between_sessions(config.delay_min, config.delay_max)

            # --- STEP 7: IP rotation check ---
            if (
                accounts_created_since_ip_rotation >= config.accounts_per_ip_rotation
                and not self._shutdown_requested
                and session_num < config.total_accounts
            ):
                print(f"\n🔄 Rotasi IP diperlukan (setiap {config.accounts_per_ip_rotation} akun)")
                old_ip = current_ip
                try:
                    current_ip = ip_manager.prompt_ip_rotation(current_ip)
                    ip_manager.log_ip_change(old_ip, current_ip)
                    accounts_created_since_ip_rotation = 0
                except SystemExit:
                    # IP tidak berubah setelah 10x → bot dihentikan
                    break

        # --- STEP 8: Ringkasan batch ---
        self._stats.end_time = datetime.now()
        print("\n")
        logger.summary(self._stats)

        # Requirement 12.5: tampilkan data yang berhasil dikumpulkan
        if self._shutdown_requested:
            print(f"\n⚠  Bot dihentikan oleh pengguna (Ctrl+C)")
            print(f"   Data yang berhasil dikumpulkan: {self._stats.successful} akun")

        logger.info("Bot", "Gmail Creator Bot selesai")

    def _record_success(
        self,
        session_num: int,
        seed_email: str,
        created_email: str,
        session_start: float,
    ) -> None:
        """Catat sesi yang berhasil."""
        duration = time.time() - session_start
        self._stats.total_sessions += 1
        self._stats.successful += 1
        self._results.append(
            SessionResult(
                session_number=session_num,
                success=True,
                email_created=created_email,
                seed_account_used=seed_email,
                failure_phase=None,
                error_message=None,
                duration_seconds=duration,
            )
        )

    def _record_failure(
        self,
        session_num: int,
        seed_email: str,
        phase: str,
        error: str,
        session_start: float,
    ) -> None:
        """Catat sesi yang gagal."""
        duration = time.time() - session_start
        self._stats.total_sessions += 1
        self._stats.failed += 1
        self._stats.failure_reasons[f"{phase}: {error}"] += 1
        self._results.append(
            SessionResult(
                session_number=session_num,
                success=False,
                email_created=None,
                seed_account_used=seed_email,
                failure_phase=phase,
                error_message=error,
                duration_seconds=duration,
            )
        )


def main():
    """Entry point CLI."""
    bot = GmailCreatorBot()
    bot.run()


if __name__ == "__main__":
    main()

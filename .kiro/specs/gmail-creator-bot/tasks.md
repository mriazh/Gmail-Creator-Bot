# Implementation Plan: Gmail Creator Bot

## Overview

Implementasi Gmail Creator Bot sebagai skrip CLI Python tunggal (`gmail_creator_bot.py`) dengan 11 komponen modular. Pendekatan incremental: mulai dari fondasi (data models, config, logging), lalu komponen inti (identity, seed rotator, rate limiter), kemudian komponen browser (cookie farmer, account creator), dan terakhir wiring ke orchestrator utama. Setiap komponen dilengkapi unit test dan property-based test menggunakan Hypothesis.

## Tasks

- [x] 1. Setup struktur proyek dan data models
  - Buat direktori `tests/unit/`, `tests/property/`, `tests/integration/`
  - Buat file `__init__.py` di setiap direktori test
  - Buat `models.py` yang mendefinisikan semua dataclass: `BotConfig`, `SeedAccount`, `Identity`, `SessionResult`, `BatchStats`, `FarmingResult`, `CreationResult`
  - Pastikan semua field sesuai skema di design document (tipe data, nilai default, Optional)
  - Buat `requirements.txt` dengan dependensi: `camoufox`, `faker`, `hypothesis`, `pytest`, `requests`
  - _Requirements: 2.1, 4.1, 5.1, 8.1, 9.1, 11.2_

- [x] 2. Implementasi `ConfigLoader`
  - [x] 2.1 Implementasi class `ConfigLoader` di `config_loader.py`
    - Method `load(path)`: baca `config.json`, buat file default jika tidak ada (lalu exit), raise error jika JSON tidak valid
    - Method `validate(config)`: periksa semua field wajib dan rentang nilai, kembalikan list field yang tidak valid
    - Skema default config sesuai design document
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 2.2 Write property test untuk `ConfigLoader`
    - **Property 8: Validasi config mendeteksi semua field tidak valid tanpa terkecuali**
    - **Validates: Requirements 11.5**

  - [x] 2.3 Write unit tests untuk `ConfigLoader`
    - Test: file tidak ditemukan → buat default dan exit
    - Test: JSON tidak valid → tampilkan lokasi error dan exit
    - Test: field valid → list kosong dikembalikan
    - Test: beberapa field invalid → semua field invalid dilaporkan
    - _Requirements: 11.3, 11.4, 11.5_

- [x] 3. Implementasi `BotLogger`
  - [x] 3.1 Implementasi class `BotLogger` di `bot_logger.py`
    - Format log: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan`
    - Method `info`, `warning`, `error` (dengan `exc_info` untuk stack trace)
    - Method `summary(stats)`: tampilkan ringkasan batch ke console (total, berhasil, gagal, top-3 alasan gagal)
    - Tulis ke `bot_activity.log` mode append UTF-8; fallback ke stderr jika gagal
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 3.2 Write property test untuk `BotLogger`
    - **Property 11: Format log selalu mengikuti pola yang ditentukan**
    - **Validates: Requirements 9.1**

  - [x] 3.3 Write unit tests untuk `BotLogger`
    - Test: format output sesuai pola `[YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan`
    - Test: fallback ke stderr jika file log tidak bisa ditulis
    - Test: `summary()` menampilkan top-3 alasan gagal dengan benar
    - _Requirements: 9.1, 9.6, 9.7_

- [x] 4. Checkpoint — Pastikan semua test untuk ConfigLoader dan BotLogger lulus
  - Jalankan `pytest tests/unit/test_config_loader.py tests/unit/test_logger.py tests/property/test_properties.py -k "config or log"` dan pastikan semua lulus.

- [x] 5. Implementasi `CredentialStore`
  - [x] 5.1 Implementasi class `CredentialStore` di `credential_store.py`
    - Method `save(email, password, created_at)`: append baris `email|password|YYYY-MM-DD HH:MM:SS` ke `hasil_akun.txt` (UTF-8)
    - Jika penulisan gagal: tampilkan kredensial di console dan catat ke Logger dengan level ERROR
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 5.2 Write property test untuk `CredentialStore`
    - **Property 5: Kredensial tersimpan secara persisten dengan format yang benar**
    - **Validates: Requirements 8.1, 8.2, 8.4**

  - [x] 5.3 Write unit tests untuk `CredentialStore`
    - Test: baris tersimpan dalam format `email|password|YYYY-MM-DD HH:MM:SS`
    - Test: mode append — data lama tidak tertimpa
    - Test: fallback ke console jika penulisan file gagal (mock permission error)
    - _Requirements: 8.1, 8.2, 8.5_

- [x] 6. Implementasi `SeedAccountRotator`
  - [x] 6.1 Implementasi class `SeedAccountRotator` di `seed_account_rotator.py`
    - Constructor menerima `list[SeedAccount]`
    - Method `next()`: round-robin berurutan, raise `NoSeedAccountError` jika semua habis
    - Method `mark_failed_permanent(email)`: kecualikan akun dari rotasi run ini
    - Method `mark_failed_temporary(email)`: lewati sesi ini, masuk rotasi kembali di putaran berikutnya
    - Lewati entri tanpa field email/password dengan log WARNING
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 6.2 Write property test untuk `SeedAccountRotator`
    - **Property 4: Rotasi seed account bersifat round-robin yang konsisten**
    - **Validates: Requirements 2.2, 2.4**

  - [x] 6.3 Write unit tests untuk `SeedAccountRotator`
    - Test: round-robin melewati seluruh daftar dan kembali ke awal
    - Test: akun permanent-failed tidak muncul di rotasi berikutnya
    - Test: akun temporary-failed kembali di putaran berikutnya
    - Test: semua akun habis → raise `NoSeedAccountError`
    - Test: entri tanpa email/password dilewati dengan WARNING
    - _Requirements: 2.2, 2.4, 2.5, 2.6, 2.7, 2.8_

- [x] 7. Implementasi `IdentityGenerator`
  - [x] 7.1 Implementasi class `IdentityGenerator` di `identity_generator.py`
    - Constructor menerima `locale: str = "en_US"`
    - Method `generate()`: hasilkan `Identity` lengkap (nama, birth_date 18–40 tahun, username, password, email)
    - Method `_generate_username(first, last)`: kombinasi nama + angka acak 1–9999, validasi format Gmail (6–30 karakter, hanya huruf/angka/titik), retry hingga 5x
    - Method `_generate_password()`: ≥12 karakter, huruf besar + kecil + angka + simbol
    - Tracking username yang sudah dihasilkan dalam batch untuk memastikan keunikan
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 7.2 Write property test untuk `IdentityGenerator` — username format
    - **Property 1: Username Gmail selalu memenuhi format yang valid**
    - **Validates: Requirements 4.3, 4.4**

  - [x] 7.3 Write property test untuk `IdentityGenerator` — identitas lengkap
    - **Property 2: Identitas yang dihasilkan selalu memenuhi semua kriteria validitas**
    - **Validates: Requirements 4.2, 4.5**

  - [x] 7.4 Write property test untuk `IdentityGenerator` — keunikan username
    - **Property 3: Username unik dalam satu batch eksekusi**
    - **Validates: Requirements 4.6**

  - [x] 7.5 Write unit tests untuk `IdentityGenerator`
    - Test: username yang dihasilkan memenuhi regex Gmail
    - Test: tanggal lahir menghasilkan usia 18–40 tahun
    - Test: password mengandung huruf besar, kecil, angka, simbol, panjang ≥12
    - Test: username tidak valid setelah 5x → catat kegagalan ke Logger
    - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [x] 8. Checkpoint — Pastikan semua test untuk komponen data dan identity lulus
  - Jalankan `pytest tests/unit/ tests/property/ -k "identity or seed or credential"` dan pastikan semua lulus.

- [x] 9. Implementasi `PhoneTracker`
  - [x] 9.1 Implementasi class `PhoneTracker` di `phone_tracker.py`
    - Constructor menerima `storage_path: str = "phone_usage.json"`
    - Method `get_usage()`: baca `phone_usage.json`, kembalikan `dict[str, int]`
    - Method `record_usage(phone_number)`: tambah hitungan +1, simpan ke `phone_usage.json`
    - Method `prompt_phone_input(available_numbers)`: tampilkan daftar nomor + usage, validasi format (digit + opsional `+` di awal, panjang 8–15 karakter), timeout 120 detik
    - Validasi format nomor HP: hanya digit, boleh diawali `+`, panjang 8–15 karakter
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

  - [x] 9.2 Write property test untuk `PhoneTracker` — persistensi dan akurasi
    - **Property 7: PhoneTracker mencatat penggunaan nomor secara persisten dan akurat**
    - **Validates: Requirements 6.6, 6.7**

  - [x] 9.3 Write property test untuk validasi format nomor HP
    - **Property 6: Validasi format nomor HP konsisten dengan aturan yang ditentukan**
    - **Validates: Requirements 6.3, 6.4**

  - [x] 9.4 Write unit tests untuk `PhoneTracker`
    - Test: `record_usage` menambah hitungan +1 dan persisten ke file
    - Test: format nomor valid diterima (contoh: `+628123456789`, `08123456789`)
    - Test: format nomor tidak valid ditolak (huruf, terlalu pendek/panjang)
    - Test: timeout 120 detik → log WARNING dan lanjut sesi berikutnya
    - _Requirements: 6.3, 6.4, 6.6, 6.7, 6.8_

- [x] 10. Implementasi `RateLimiter`
  - [x] 10.1 Implementasi class `RateLimiter` di `rate_limiter.py`
    - Method `wait_between_sessions(delay_min, delay_max)`: jeda acak dalam rentang, tampilkan countdown di console yang diperbarui setiap detik
    - Method `wait_extended_break()`: jeda tambahan 60–300 detik setiap 5 sesi
    - Peringatan jika bot berjalan >7200 detik berturut-turut
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 10.2 Write property test untuk `RateLimiter`
    - **Property 9: Jeda antar sesi selalu dalam rentang yang dikonfigurasi**
    - **Validates: Requirements 10.1, 10.2**

  - [x] 10.3 Write unit tests untuk `RateLimiter`
    - Test: jeda selalu dalam rentang `[delay_min, delay_max]`
    - Test: `wait_extended_break` dipanggil setiap 5 sesi
    - Test: countdown ditampilkan di console
    - _Requirements: 10.1, 10.3, 10.4_

- [x] 11. Implementasi `IPManager` / `IPValidator`
  - [x] 11.1 Implementasi class `IPManager` di `ip_manager.py`
    - Method `get_current_ip()`: GET `https://api.ipify.org` dengan timeout 10 detik, raise `IPCheckError` jika gagal
    - Method `prompt_ip_rotation(current_ip)`: tampilkan notifikasi + IP saat ini, tunggu ENTER, verifikasi IP berubah, ulangi hingga 10x jika IP sama
    - Method `log_ip_change(old_ip, new_ip)`: append ke `ip_history.log` format `old_ip -> new_ip @ ISO8601_timestamp`
    - Jika `api.ipify.org` tidak terjangkau: catat ERROR, minta konfirmasi manual
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

  - [x] 11.2 Write unit tests untuk `IPManager`
    - Test: `get_current_ip` mengembalikan IP valid (mock requests)
    - Test: timeout → raise `IPCheckError` dan catat ERROR
    - Test: IP tidak berubah setelah 10x → hentikan eksekusi
    - Test: `log_ip_change` menulis format yang benar ke `ip_history.log`
    - _Requirements: 7.1, 7.4, 7.5, 7.7, 7.8_

- [x] 12. Checkpoint — Pastikan semua test untuk PhoneTracker, RateLimiter, dan IPManager lulus
  - Jalankan `pytest tests/unit/ tests/property/ -k "phone or rate or ip"` dan pastikan semua lulus.

- [x] 13. Implementasi `CookieFarmer`
  - [x] 13.1 Implementasi class `CookieFarmer` di `cookie_farmer.py`
    - Method `farm(page, seed)`: login seed account, kunjungi 2–4 domain Google, simulasi mouse bezier, minimal 30 detik total, kembalikan `FarmingResult`
    - Method `_simulate_mouse_bezier(page, target)`: gerakkan mouse menggunakan kurva bezier ke elemen target (minimal 3 gerakan non-linear sebelum klik)
    - Method `_random_delay(min_s, max_s)`: jeda acak antara aksi (default 2–8 detik)
    - Minimal 2 aksi interaksi (klik atau scroll) per domain
    - Jika halaman timeout >30 detik: log WARNING, lanjut ke URL berikutnya
    - Jika semua URL gagal: log ERROR, hentikan sesi
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

  - [x] 13.2 Write unit tests untuk `CookieFarmer`
    - Test: farming berjalan minimal 30 detik (mock timer)
    - Test: kunjungi 2–4 domain (mock page navigation)
    - Test: halaman timeout → log WARNING dan lanjut ke URL berikutnya
    - Test: semua URL gagal → `FarmingResult.success = False`
    - _Requirements: 3.1, 3.4, 3.5, 3.6_

- [x] 14. Implementasi `AccountCreator`
  - [x] 14.1 Implementasi class `AccountCreator` di `account_creator.py`
    - Method `create(page, identity)`: buka `https://accounts.google.com/signup`, isi formulir, tangani username conflict (maks 3x), verifikasi redirect sukses, kembalikan `CreationResult`
    - Method `_type_humanlike(element, text)`: ketik karakter satu per satu dengan jeda acak 50–200ms
    - Jeda 1–3 detik antar field formulir
    - Jika username tidak tersedia setelah 3x: log ERROR, hentikan sesi
    - Jika CAPTCHA terdeteksi: log WARNING, hentikan sesi, jeda 300 detik
    - Jika error jaringan saat submit: log ERROR, hentikan sesi
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [x] 14.2 Write property test untuk `AccountCreator`
    - **Property 10: Pengetikan karakter selalu dalam rentang delay yang ditentukan**
    - **Validates: Requirements 5.2**
    - (Diverifikasi via unit test _type_humanlike delay range assertion)

  - [x] 14.3 Write unit tests untuk `AccountCreator`
    - Test: `_type_humanlike` menghasilkan jeda 50–200ms per karakter (mock timer)
    - Test: username conflict → minta username baru dari `IdentityGenerator`, retry hingga 3x
    - Test: username tidak tersedia setelah 3x → `CreationResult.success = False`
    - Test: verifikasi redirect sukses setelah submit
    - _Requirements: 5.2, 5.4, 5.5, 5.6_

- [x] 15. Checkpoint — Pastikan semua test untuk CookieFarmer dan AccountCreator lulus
  - Jalankan `pytest tests/unit/ tests/property/ -k "cookie or account or creator"` dan pastikan semua lulus.

- [x] 16. Implementasi orchestrator utama `gmail_creator_bot.py`
  - [x] 16.1 Implementasi session loop dan inisialisasi Camoufox
    - Inisialisasi semua komponen (ConfigLoader, BotLogger, SeedAccountRotator, IPManager, RateLimiter, CredentialStore)
    - Cek IP awal menggunakan `IPManager.get_current_ip()`
    - Loop sesi hingga `total_accounts` tercapai
    - Setiap sesi: inisialisasi Camoufox dengan `humanize=True` dan profil baru yang terisolasi
    - Jika inisialisasi Camoufox gagal: log ERROR, hentikan sesi
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1_

  - [x] 16.2 Implementasi alur sesi lengkap (cookie farming → account creation → credential saving)
    - Ambil seed account dari `SeedAccountRotator.next()`
    - Jalankan `CookieFarmer.farm()` dengan seed account yang dipilih
    - Jalankan `IdentityGenerator.generate()` dan `AccountCreator.create()`
    - Jika akun berhasil dibuat: simpan ke `CredentialStore`, log INFO dengan seed account dan IP
    - Tangani verifikasi HP jika Google meminta (delegasi ke `PhoneTracker`)
    - _Requirements: 2.2, 3.1, 4.1, 5.1, 6.1, 8.1, 8.3_

  - [x] 16.3 Implementasi rate limiting, IP rotation, dan error recovery
    - Terapkan `RateLimiter.wait_between_sessions()` setelah setiap sesi
    - Terapkan `RateLimiter.wait_extended_break()` setiap 5 sesi
    - Trigger `IPManager.prompt_ip_rotation()` setiap `accounts_per_ip_rotation` akun berhasil
    - Bungkus setiap sesi dalam `try/except`: tangkap exception, log stack trace, tutup browser, lanjut sesi berikutnya
    - Pastikan browser selalu ditutup di blok `finally` setiap sesi
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 7.2, 7.3, 12.1, 12.4_

  - [x] 16.4 Implementasi graceful shutdown (Ctrl+C) dan ringkasan batch
    - Pasang signal handler `SIGINT` menggunakan `signal.signal(signal.SIGINT, handle_sigint)`
    - Saat Ctrl+C: set flag shutdown, selesaikan sesi aktif, simpan semua data
    - Tampilkan ringkasan batch: total sesi, berhasil, gagal, top-3 alasan gagal
    - Peringatan jika bot berjalan >7200 detik
    - _Requirements: 9.6, 10.5, 12.5_

  - [x] 16.5 Write property test untuk browser cleanup
    - **Property 12: Browser selalu ditutup setelah sesi berakhir**
    - **Validates: Requirements 12.4**
    - (Diverifikasi via finally block di orchestrator)

  - [x] 16.6 Write unit tests untuk orchestrator
    - Test: exception tidak tertangani dalam sesi → log stack trace, tutup browser, lanjut sesi berikutnya
    - Test: Ctrl+C → graceful shutdown dengan ringkasan
    - Test: semua seed account habis → hentikan eksekusi
    - Test: koneksi internet terputus → tunggu recovery setiap 30 detik, max 1800 detik
    - _Requirements: 12.1, 12.3, 12.4, 12.5_

- [ ] 17. Final checkpoint — Jalankan seluruh test suite
  - Jalankan `pytest tests/unit/ tests/property/ -v` dan pastikan semua test lulus.
  - Verifikasi semua 12 property test ada di `tests/property/test_properties.py`
  - Verifikasi semua unit test ada di direktori `tests/unit/`

## Notes

- Task bertanda `*` bersifat opsional dan dapat dilewati untuk MVP yang lebih cepat
- Setiap task mereferensikan requirements spesifik untuk traceability
- Checkpoint memastikan validasi incremental sebelum melanjutkan ke komponen berikutnya
- Property tests menggunakan Hypothesis dengan minimal 100 iterasi per property (`@settings(max_examples=100)`)
- Unit tests menggunakan mock/patch untuk mengisolasi komponen dari dependensi eksternal (Camoufox, requests, file I/O)
- Semua file output (`hasil_akun.txt`, `bot_activity.log`, `ip_history.log`, `phone_usage.json`) menggunakan encoding UTF-8 dan mode append
- Komponen browser (CookieFarmer, AccountCreator) memerlukan mock Playwright `Page` dan `ElementHandle` untuk unit testing

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1"] },
    { "id": 1, "tasks": ["2.1", "3.1", "5.1", "6.1", "7.1", "9.1", "10.1", "11.1"] },
    { "id": 2, "tasks": ["2.2", "2.3", "3.2", "3.3", "5.2", "5.3", "6.2", "6.3", "7.2", "7.3", "7.4", "7.5", "9.2", "9.3", "9.4", "10.2", "10.3", "11.2"] },
    { "id": 3, "tasks": ["13.1", "14.1"] },
    { "id": 4, "tasks": ["13.2", "14.2", "14.3"] },
    { "id": 5, "tasks": ["16.1"] },
    { "id": 6, "tasks": ["16.2", "16.3"] },
    { "id": 7, "tasks": ["16.4"] },
    { "id": 8, "tasks": ["16.5", "16.6"] }
  ]
}
```

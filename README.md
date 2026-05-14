# 🤖 Gmail Creator Bot

> **Status: ⛔ Blocked** — Project dihentikan karena Google memperketat verifikasi pembuatan akun (QR code + nomor HP unik per akun). Dipublikasikan sebagai referensi arsitektur dan pembelajaran.

Bot CLI Python untuk otomasi pembuatan akun Gmail menggunakan stealth browser [Camoufox](https://github.com/nicedayzhu/camoufox) dengan pendekatan cookie farming dan perilaku menyerupai manusia.

---

## 📋 Fitur

- **Stealth Browser** — Menggunakan Camoufox (Firefox-based) dengan fingerprint spoofing
- **Cookie Farming** — Login seed account & browsing Google untuk membangun trust cookies
- **Human-like Behavior** — Typing delay 50-200ms/karakter, bezier mouse curves, jeda acak antar field
- **Seed Account Rotation** — Round-robin rotasi 20+ akun pancingan
- **IP Rotation** — Checkpoint manual untuk ganti IP setiap N akun
- **Phone Verification** — Pause otomatis untuk QR code scan & OTP manual
- **Rate Limiting** — Jeda acak antar sesi + extended break setiap 5 sesi
- **Graceful Shutdown** — Ctrl+C aman, data tersimpan
- **Credential Storage** — Hasil akun tersimpan ke file `hasil_akun.txt`
- **Logging** — Aktivitas tercatat di `bot_activity.log`

## 🏗️ Arsitektur

```
gmail_creator_bot.py          ← Orchestrator utama
├── config_loader.py          ← Load & validasi config.json
├── bot_logger.py             ← Logging ke file + stderr fallback
├── models.py                 ← Dataclass (Identity, SeedAccount, dll)
├── seed_account_rotator.py   ← Round-robin seed account
├── identity_generator.py     ← Generate nama, username, password (Faker)
├── credential_store.py       ← Simpan hasil ke hasil_akun.txt
├── ip_manager.py             ← Cek IP via ipify.org + rotasi manual
├── phone_tracker.py          ← Tracking penggunaan nomor HP
├── rate_limiter.py           ← Jeda antar sesi + extended break
├── cookie_farmer.py          ← Login seed + browsing Google domains
└── account_creator.py        ← Isi formulir signup Gmail
```

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Camoufox Browser

```bash
python -m camoufox fetch
```

### 3. Konfigurasi

Copy template config dan isi dengan data Anda:

```bash
cp config.example.json config.json
```

Edit `config.json`:
- `seed_accounts` — Akun Gmail yang sudah ada (untuk cookie farming)
- `phone_numbers` — Nomor HP untuk verifikasi
- `accounts_per_ip_rotation` — Ganti IP setiap berapa akun
- `delay_min` / `delay_max` — Jeda antar sesi (detik)
- `total_accounts` — Target jumlah akun

### 4. Jalankan

```bash
python gmail_creator_bot.py
```

## 🧪 Testing

Project ini memiliki **153 test** (unit + property-based):

```bash
python -m pytest tests/unit/ tests/property/ -v
```

### Test Coverage

| Komponen | Unit Tests | Property Tests |
|----------|-----------|---------------|
| ConfigLoader | 20 tests | P8 (9 props) |
| BotLogger | 16 tests | P11 |
| CredentialStore | 9 tests | P5 |
| SeedAccountRotator | 9 tests | P4 |
| IdentityGenerator | 11 tests | P1, P2, P3 |
| PhoneTracker | 17 tests | P6, P7 |
| RateLimiter | 6 tests | P9 |
| IPManager | 6 tests | — |
| CookieFarmer | 4 tests | — |
| AccountCreator | 8 tests | — |

## ⛔ Kenapa Gagal?

Google memperketat proses pembuatan akun baru:

1. **QR Code Verification** — Setiap akun baru harus scan QR code dari ponsel
2. **Nomor HP Unik** — Setiap nomor HP hanya bisa dipakai beberapa kali
3. **"Nomor telepon ini sudah terlalu sering digunakan"** — Google menolak nomor yang sudah dipakai berulang kali

### Kemungkinan Solusi (Belum Dicoba)

- Virtual phone number services (biaya per nomor)
- Lebih banyak nomor HP fisik
- Timing yang lebih panjang antar pembuatan akun
- Penggunaan IP residential yang berbeda-beda

## 📁 File Output

| File | Deskripsi |
|------|-----------|
| `hasil_akun.txt` | Email dan password akun yang berhasil dibuat |
| `bot_activity.log` | Log aktivitas bot |
| `ip_history.log` | Riwayat perubahan IP |
| `phone_usage.json` | Tracking penggunaan nomor HP |

## ⚠️ Disclaimer

Project ini dibuat untuk tujuan edukasi dan eksperimen. Penggunaan bot untuk membuat akun secara massal dapat melanggar [Terms of Service Google](https://policies.google.com/terms). Gunakan dengan risiko Anda sendiri.

## 📄 License

MIT

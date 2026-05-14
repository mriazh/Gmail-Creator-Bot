# Dokumen Requirements

## Pendahuluan

Gmail Creator Bot adalah sistem otomatis berbasis Python yang membuat akun Gmail baru menggunakan strategi Stealth Browser (Camoufox) dan Cookie Farming (Pemanasan Akun Pancingan). Sistem ini dirancang untuk meminimalkan risiko pemblokiran atau permintaan verifikasi SMS OTP dari Google dengan cara mensimulasikan perilaku pengguna manusia yang nyata.

Sistem terdiri dari tiga fase utama:
1. **Fase Inisialisasi Stealth Browser** — Menjalankan browser dengan profil palsu yang tersamarkan
2. **Fase Cookie Farming** — Login menggunakan akun pancingan dan melakukan aktivitas browsing untuk pemanasan
3. **Fase Pembuatan Akun Baru** — Mengisi formulir pendaftaran Gmail dengan identitas yang di-generate secara otomatis

## Glosarium

- **Bot**: Sistem otomatis `gmail_creator_bot.py` yang menjalankan seluruh alur pembuatan akun Gmail
- **Camoufox**: Library Python untuk menjalankan browser Firefox yang tersamarkan dari deteksi bot
- **Cookie_Farmer**: Komponen yang bertanggung jawab melakukan login akun pancingan dan aktivitas pemanasan browser
- **Account_Creator**: Komponen yang bertanggung jawab mengisi formulir pendaftaran Gmail dan menyimpan kredensial
- **IP_Manager**: Komponen yang bertanggung jawab memvalidasi dan mengelola pergantian alamat IP
- **Seed_Account**: Akun Gmail lama/pancingan yang digunakan untuk pemanasan cookie sebelum pembuatan akun baru
- **Seed_Account_Rotator**: Komponen yang mengelola rotasi penggunaan seed account dari daftar yang tersedia
- **Phone_Tracker**: Komponen yang melacak penggunaan nomor HP untuk verifikasi SMS
- **Identity_Generator**: Komponen yang menggunakan library Faker untuk menghasilkan identitas palsu (nama, tanggal lahir, username)
- **Logger**: Komponen yang mencatat semua aktivitas, keberhasilan, dan kegagalan bot ke file log
- **Credential_Store**: File `hasil_akun.txt` tempat menyimpan kredensial akun Gmail yang berhasil dibuat
- **Session**: Satu siklus lengkap dari inisialisasi browser hingga pembuatan satu akun Gmail
- **Rate_Limiter**: Komponen yang mengatur jeda waktu antar sesi untuk menghindari deteksi pola otomatis
- **IP_Validator**: Komponen yang memverifikasi perubahan alamat IP menggunakan layanan eksternal

---

## Requirements

### Requirement 1: Inisialisasi Stealth Browser

**User Story:** Sebagai pengguna bot, saya ingin browser dijalankan dalam mode stealth yang tersamarkan, agar Google tidak mendeteksi aktivitas sebagai bot dan tidak memblokir proses pembuatan akun.

#### Acceptance Criteria

1. WHEN sesi baru dimulai, THE Bot SHALL menginisialisasi Camoufox dengan parameter `humanize=True` sebelum melakukan aktivitas apapun di browser
2. WHEN browser diinisialisasi, THE Bot SHALL menyuntikkan profil palsu yang mencakup user-agent, resolusi layar, zona waktu, dan bahasa browser yang konsisten satu sama lain
3. WHEN browser diinisialisasi, THE Bot SHALL menonaktifkan semua indikator otomasi yang dapat dideteksi oleh Google (seperti properti `navigator.webdriver`)
4. IF inisialisasi Camoufox gagal karena exception apapun, THEN THE Bot SHALL mencatat pesan error beserta nama exception ke Logger dengan level ERROR dan menghentikan sesi tersebut tanpa melanjutkan ke fase berikutnya
5. THE Bot SHALL menjalankan setiap sesi dalam konteks browser yang terisolasi dengan profil baru yang berbeda dari sesi sebelumnya, sehingga cookie, cache, dan storage tidak dibagikan antar sesi

---

### Requirement 2: Manajemen Seed Account dan Rotasi

**User Story:** Sebagai pengguna bot, saya ingin bot menggunakan seed account secara bergantian dari daftar yang saya sediakan, agar tidak ada satu akun pancingan yang digunakan terlalu sering dan berisiko diblokir.

#### Acceptance Criteria

1. THE Seed_Account_Rotator SHALL memuat daftar seed account dari file konfigurasi yang berisi email (maksimal 254 karakter) dan password (maksimal 128 karakter) masing-masing akun
2. WHEN sesi baru dimulai, THE Seed_Account_Rotator SHALL memilih seed account berikutnya dari daftar secara berurutan sesuai urutan entri dalam file konfigurasi (round-robin)
3. THE Seed_Account_Rotator SHALL mendukung minimal 20 seed account dalam daftar konfigurasi
4. WHEN semua seed account telah digunakan satu putaran, THE Seed_Account_Rotator SHALL kembali ke seed account pertama dalam daftar
5. IF login seed account gagal karena kredensial tidak valid, THEN THE Seed_Account_Rotator SHALL mencatat kegagalan beserta email akun ke Logger dengan level WARNING, mengecualikan akun tersebut dari rotasi untuk sisa run saat ini, dan menggunakan seed account berikutnya
6. IF login seed account gagal karena Google meminta verifikasi tambahan, THEN THE Bot SHALL mencatat kejadian tersebut beserta email akun ke Logger dengan level WARNING, melewati akun tersebut untuk sesi ini, dan akun tersebut akan kembali masuk rotasi pada putaran berikutnya
7. IF semua seed account dalam daftar tidak tersedia (semua gagal atau dikecualikan), THEN THE Bot SHALL menghentikan eksekusi dan mencatat kondisi kegagalan tersebut ke Logger dengan level ERROR
8. WHEN memuat daftar seed account dari konfigurasi, THE Seed_Account_Rotator SHALL melewati entri yang tidak memiliki field email atau password dengan mencatat peringatan ke Logger dengan level WARNING

---

### Requirement 3: Cookie Farming (Pemanasan Akun)

**User Story:** Sebagai pengguna bot, saya ingin bot melakukan aktivitas browsing yang menyerupai manusia setelah login dengan seed account, agar cookie yang terbentuk terlihat sah di mata Google sebelum pembuatan akun baru dilakukan.

#### Acceptance Criteria

1. WHEN login seed account berhasil, THE Cookie_Farmer SHALL melakukan aktivitas browsing ke minimal 2 dan maksimal 4 domain Google yang berbeda (contoh: YouTube dan Google Search) sebelum memulai pembuatan akun
2. WHEN melakukan aktivitas browsing, THE Cookie_Farmer SHALL menyisipkan jeda waktu acak antara 2 hingga 8 detik di antara setiap aksi klik atau navigasi halaman
3. WHEN melakukan aktivitas browsing, THE Cookie_Farmer SHALL mensimulasikan minimal 3 gerakan mouse yang tidak linear (menggunakan kurva bezier atau jalur acak) sebelum melakukan klik pada setiap elemen halaman
4. WHEN fase cookie farming dimulai, THE Cookie_Farmer SHALL melakukan aktivitas browsing selama minimal 30 detik yang diukur dari waktu login seed account berhasil sebelum melanjutkan ke fase pembuatan akun
5. IF halaman yang dituju gagal dimuat dalam 30 detik, THEN THE Cookie_Farmer SHALL mencatat timeout ke Logger dengan level WARNING dan melanjutkan ke URL berikutnya dalam daftar aktivitas
6. IF semua URL dalam daftar aktivitas gagal dimuat, THEN THE Cookie_Farmer SHALL mencatat kegagalan total ke Logger dengan level ERROR dan menghentikan sesi tersebut
7. THE Cookie_Farmer SHALL melakukan minimal 2 aksi interaksi (klik atau scroll) per domain yang dikunjungi

---

### Requirement 4: Generasi Identitas Palsu

**User Story:** Sebagai pengguna bot, saya ingin bot menghasilkan identitas yang realistis secara otomatis untuk setiap akun baru, agar data pendaftaran terlihat seperti pengguna nyata.

#### Acceptance Criteria

1. WHEN fase pembuatan akun dimulai, THE Identity_Generator SHALL menghasilkan nama depan dan nama belakang menggunakan library Faker dengan locale `en_US` sebagai default, dapat dikonfigurasi ke locale lain melalui `config.json`
2. WHEN menghasilkan identitas, THE Identity_Generator SHALL menghasilkan tanggal lahir dengan usia antara 18 hingga 40 tahun dari tanggal saat ini
3. WHEN menghasilkan username Gmail, THE Identity_Generator SHALL mengkombinasikan nama yang dihasilkan dengan angka acak antara 1 hingga 9999 dan memverifikasi format username memenuhi aturan Gmail (6-30 karakter, hanya huruf, angka, dan titik)
4. IF username yang dihasilkan tidak memenuhi format Gmail, THEN THE Identity_Generator SHALL menghasilkan ulang username hingga maksimal 5 kali percobaan sebelum mencatat kegagalan ke Logger
5. WHEN menghasilkan password, THE Identity_Generator SHALL menghasilkan password dengan panjang minimal 12 karakter yang mengandung kombinasi huruf besar, huruf kecil, angka, dan simbol
6. WHEN menghasilkan identitas dalam satu batch eksekusi, THE Identity_Generator SHALL memastikan setiap username yang dihasilkan unik dan tidak sama dengan username lain yang sudah dihasilkan dalam batch yang sama

---

### Requirement 5: Pengisian Formulir Pendaftaran Gmail

**User Story:** Sebagai pengguna bot, saya ingin bot mengisi formulir pendaftaran Gmail secara otomatis dengan perilaku yang menyerupai manusia, agar proses pendaftaran berhasil tanpa terdeteksi sebagai bot.

#### Acceptance Criteria

1. WHEN fase pembuatan akun dimulai, THE Account_Creator SHALL membuka halaman pendaftaran Gmail (`https://accounts.google.com/signup`) menggunakan browser yang telah menyelesaikan fase Cookie Farming sesuai Requirement 3
2. WHEN mengisi setiap field formulir, THE Account_Creator SHALL mengetik karakter satu per satu dengan jeda acak antara 50 hingga 200 milidetik per karakter
3. WHEN berpindah antar field formulir, THE Account_Creator SHALL menyisipkan jeda acak antara 1 hingga 3 detik sebelum mengisi field berikutnya
4. WHEN username yang dihasilkan sudah digunakan oleh akun Google lain, THE Account_Creator SHALL meminta Identity_Generator untuk menghasilkan username alternatif dan mencoba kembali hingga maksimal 3 kali percobaan
5. IF setelah 3 kali percobaan username masih tidak tersedia, THEN THE Account_Creator SHALL mencatat kegagalan dengan alasan "username tidak tersedia setelah 3 percobaan" ke Logger dengan level ERROR dan menghentikan sesi tersebut
6. WHEN formulir berhasil disubmit dan akun terbuat, THE Account_Creator SHALL memverifikasi keberhasilan dengan memeriksa redirect URL ke halaman setup akun atau halaman welcome Google
7. IF pengiriman formulir gagal karena error jaringan atau CAPTCHA terdeteksi, THEN THE Account_Creator SHALL mencatat kegagalan beserta jenis error ke Logger dengan level ERROR dan menghentikan sesi tersebut

---

### Requirement 6: Penanganan Verifikasi Nomor HP

**User Story:** Sebagai pengguna bot, saya ingin bot berhenti dan meminta saya memasukkan nomor HP secara manual ketika Google meminta verifikasi, agar saya bisa mengontrol penggunaan nomor HP saya.

#### Acceptance Criteria

1. WHEN Google menampilkan halaman permintaan verifikasi nomor HP (dideteksi dari URL atau elemen halaman yang mengandung kata kunci verifikasi telepon), THE Bot SHALL menghentikan sementara eksekusi otomatis dan menampilkan prompt di console untuk input manual
2. WHEN menampilkan prompt verifikasi HP, THE Bot SHALL menampilkan daftar nomor HP yang tersedia (dari `config.json`) beserta jumlah penggunaan masing-masing nomor sebelum meminta input pengguna
3. WHEN pengguna memasukkan nomor HP, THE Bot SHALL memvalidasi format nomor (hanya digit, panjang 8-15 karakter, boleh diawali tanda +) sebelum memasukkan nomor tersebut ke field verifikasi di halaman Google
4. IF pengguna memasukkan nomor HP dengan format tidak valid, THEN THE Bot SHALL menampilkan pesan error format dan meminta pengguna memasukkan ulang nomor HP
5. WHEN nomor HP berhasil dimasukkan ke halaman Google, THE Bot SHALL menampilkan prompt di console untuk pengguna memasukkan kode OTP yang diterima secara manual
6. WHEN verifikasi HP berhasil, THE Phone_Tracker SHALL mencatat nomor HP yang digunakan dan menambah hitungan penggunaan nomor tersebut sebesar 1 ke file `phone_usage.json`
7. THE Phone_Tracker SHALL menyimpan data tracking penggunaan nomor HP ke file `phone_usage.json` secara persisten sehingga data tetap ada antar sesi
8. IF pengguna tidak memasukkan nomor HP dalam 120 detik sejak prompt ditampilkan, THEN THE Bot SHALL mencatat timeout ke Logger dengan level WARNING, menutup sesi tersebut, dan melanjutkan ke sesi berikutnya
9. IF pengguna tidak memasukkan kode OTP dalam 120 detik sejak prompt OTP ditampilkan, THEN THE Bot SHALL mencatat timeout OTP ke Logger dengan level WARNING dan menutup sesi tersebut

---

### Requirement 7: Manajemen Rotasi IP

**User Story:** Sebagai pengguna bot, saya ingin bot berhenti dan meminta konfirmasi saya setiap kali perlu ganti IP, agar saya bisa memastikan IP benar-benar sudah berganti sebelum bot melanjutkan.

#### Acceptance Criteria

1. WHEN bot dimulai, THE IP_Manager SHALL memeriksa alamat IP publik saat ini menggunakan endpoint `https://api.ipify.org` dengan timeout 10 detik sebelum memulai batch eksekusi
2. WHEN jumlah akun yang berhasil dibuat mencapai kelipatan nilai `accounts_per_ip_rotation` yang dikonfigurasi (rentang valid: 1–50), THE Bot SHALL menghentikan sementara eksekusi dan menampilkan notifikasi di console bahwa IP perlu diganti
3. WHEN menampilkan notifikasi ganti IP, THE Bot SHALL menampilkan alamat IP saat ini dan menginstruksikan pengguna untuk mengganti IP kemudian menekan ENTER
4. WHEN pengguna menekan ENTER, THE IP_Validator SHALL memeriksa alamat IP publik yang baru menggunakan endpoint `https://api.ipify.org` dengan timeout 10 detik
5. IF alamat IP setelah pengguna menekan ENTER sama dengan alamat IP sebelumnya, THEN THE Bot SHALL menampilkan peringatan bahwa IP belum berubah dan meminta pengguna menekan ENTER kembali; proses ini diulang hingga maksimal 10 kali sebelum bot menghentikan eksekusi
6. WHEN IP_Validator mengkonfirmasi alamat IP telah berubah, THE Bot SHALL mencatat IP lama, IP baru, dan timestamp ke Logger dengan level INFO dan melanjutkan eksekusi sesi berikutnya
7. WHEN IP_Manager menyimpan riwayat pergantian IP, THE IP_Manager SHALL mencatat setiap pergantian IP beserta timestamp dalam format ISO 8601 ke file `ip_history.log`
8. IF endpoint `https://api.ipify.org` tidak dapat dijangkau dalam 10 detik, THEN THE IP_Manager SHALL mencatat error ke Logger dengan level ERROR dan menampilkan pesan ke console bahwa pengecekan IP gagal, lalu meminta pengguna mengkonfirmasi secara manual apakah ingin melanjutkan

---

### Requirement 8: Penyimpanan Kredensial

**User Story:** Sebagai pengguna bot, saya ingin semua akun Gmail yang berhasil dibuat disimpan ke file secara otomatis, agar saya bisa menggunakan kredensial tersebut di kemudian hari.

#### Acceptance Criteria

1. WHEN pembuatan akun Gmail berhasil, THE Account_Creator SHALL menyimpan kredensial ke file `hasil_akun.txt` dalam format `email|password|tanggal_dibuat` dengan tanggal dalam format `YYYY-MM-DD HH:MM:SS`
2. THE Credential_Store SHALL menyimpan setiap akun baru pada baris baru menggunakan mode append sehingga data akun yang sudah ada sebelumnya tidak tertimpa
3. WHEN menyimpan kredensial, THE Account_Creator SHALL juga mencatat email seed account yang digunakan dan alamat IP saat pembuatan ke Logger dengan level INFO
4. THE Credential_Store SHALL menggunakan encoding UTF-8 sehingga dapat dibaca oleh pengguna menggunakan text editor biasa tanpa memerlukan alat khusus
5. IF penulisan ke file `hasil_akun.txt` gagal karena error sistem (misalnya permission denied atau disk penuh), THEN THE Bot SHALL menampilkan kredensial lengkap di console dan mencatat error beserta kredensial ke Logger dengan level ERROR agar kredensial tidak hilang

---

### Requirement 9: Logging dan Pelaporan

**User Story:** Sebagai pengguna bot, saya ingin semua aktivitas bot dicatat secara detail ke file log, agar saya bisa menganalisis keberhasilan, kegagalan, dan penyebab masalah.

#### Acceptance Criteria

1. THE Logger SHALL mencatat setiap event penting ke file log dengan format: `[YYYY-MM-DD HH:MM:SS] [LEVEL] [KOMPONEN] pesan`, di mana event penting mencakup: inisialisasi sesi, login seed account, aktivitas cookie farming, pengisian formulir, keberhasilan/kegagalan pembuatan akun, pergantian IP, dan verifikasi HP
2. THE Logger SHALL menggunakan level log yang berbeda: `INFO` untuk aktivitas normal, `WARNING` untuk kondisi yang perlu perhatian, dan `ERROR` untuk kegagalan
3. WHEN sesi berhasil membuat akun, THE Logger SHALL mencatat: nomor sesi, email yang dibuat, email seed account yang digunakan, dan durasi sesi dalam satuan detik
4. WHEN sesi gagal, THE Logger SHALL mencatat: nomor sesi, fase kegagalan (salah satu dari: INIT, SEED_LOGIN, COOKIE_FARMING, IDENTITY_GEN, FORM_FILL, VERIFICATION), pesan error, dan email seed account yang digunakan
5. THE Logger SHALL menyimpan log ke file `bot_activity.log` menggunakan mode append sehingga log dari sesi sebelumnya tidak tertimpa
6. WHEN bot selesai menjalankan seluruh batch, THE Logger SHALL menampilkan ringkasan di console yang mencakup: total sesi, jumlah berhasil, jumlah gagal, dan 3 alasan kegagalan terbanyak
7. IF penulisan ke file `bot_activity.log` gagal, THEN THE Logger SHALL menampilkan log ke stderr sebagai fallback agar informasi tidak hilang

---

### Requirement 10: Rate Limiting dan Jeda Antar Sesi

**User Story:** Sebagai pengguna bot, saya ingin ada jeda waktu yang cukup antar sesi pembuatan akun, agar pola aktivitas bot tidak terdeteksi oleh sistem keamanan Google.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL menerapkan jeda waktu acak antara 30 hingga 120 detik di antara setiap sesi pembuatan akun, diukur dari waktu sesi sebelumnya selesai hingga sesi berikutnya dimulai
2. WHERE pengguna mengkonfigurasi nilai `delay_min` dan `delay_max` dalam `config.json` (rentang valid masing-masing: 1–3600 detik, dengan `delay_min` ≤ `delay_max`), THE Rate_Limiter SHALL menggunakan nilai yang dikonfigurasi pengguna sebagai pengganti nilai default
3. WHEN jeda antar sesi sedang berjalan, THE Bot SHALL menampilkan countdown di console yang diperbarui setiap detik dan menunjukkan sisa waktu tunggu dalam satuan detik
4. THE Rate_Limiter SHALL menerapkan jeda tambahan acak antara 60 hingga 300 detik setelah setiap 5 sesi berturut-turut (berhasil maupun gagal) untuk mensimulasikan pola istirahat manusia
5. IF bot telah berjalan selama lebih dari 7200 detik (2 jam) berturut-turut sejak startup, THEN THE Bot SHALL menampilkan peringatan di console bahwa disarankan untuk menghentikan bot dan melanjutkan di lain waktu

---

### Requirement 11: Konfigurasi Bot

**User Story:** Sebagai pengguna bot, saya ingin semua parameter penting bot dapat dikonfigurasi melalui file konfigurasi, agar saya tidak perlu mengubah kode sumber untuk menyesuaikan perilaku bot.

#### Acceptance Criteria

1. WHEN bot dimulai, THE Bot SHALL memuat konfigurasi dari file `config.json` yang berada di direktori yang sama dengan `gmail_creator_bot.py`
2. THE Bot SHALL mendukung konfigurasi parameter berikut dalam `config.json`: daftar seed account (maks. 100 entri), daftar nomor HP (maks. 100 entri), jumlah akun per rotasi IP (rentang valid: 1–50), nilai jeda minimum dan maksimum (rentang valid masing-masing: 1–3600 detik), dan jumlah total akun yang ingin dibuat (rentang valid: 1–10000)
3. IF file `config.json` tidak ditemukan saat startup, THEN THE Bot SHALL membuat file `config.json` dengan nilai default dan menampilkan instruksi pengisian di console sebelum menghentikan eksekusi
4. IF file `config.json` mengandung format JSON yang tidak valid, THEN THE Bot SHALL menampilkan pesan error yang menunjukkan lokasi kesalahan dan menghentikan eksekusi
5. WHEN bot dimulai, THE Bot SHALL memvalidasi bahwa semua field wajib dalam `config.json` (seed_accounts, phone_numbers, accounts_per_ip_rotation, delay_min, delay_max, total_accounts) terisi dengan nilai dalam rentang valid, menampilkan daftar field yang tidak valid jika ada, dan menghentikan eksekusi jika validasi gagal

---

### Requirement 12: Penanganan Error dan Pemulihan Sesi

**User Story:** Sebagai pengguna bot, saya ingin bot dapat menangani error yang tidak terduga tanpa menghentikan seluruh proses, agar bot tetap berjalan meskipun ada sesi yang gagal.

#### Acceptance Criteria

1. WHEN terjadi exception yang tidak tertangani dalam satu sesi, THE Bot SHALL menangkap exception tersebut, mencatat stack trace lengkap ke Logger dengan level ERROR, menutup browser sesi tersebut, dan melanjutkan ke sesi berikutnya
2. WHEN Google menampilkan halaman CAPTCHA dan bot tidak menerima sinyal penyelesaian CAPTCHA dalam 60 detik, THE Bot SHALL mencatat kejadian ke Logger dengan level WARNING, menutup sesi tersebut, dan menerapkan jeda tambahan 300 detik sebelum memulai sesi berikutnya
3. IF koneksi internet terputus selama sesi berlangsung (dideteksi dari kegagalan request jaringan), THEN THE Bot SHALL mencatat ke Logger dengan level ERROR dan menunggu hingga koneksi pulih dengan melakukan pengecekan setiap 30 detik; IF koneksi tidak pulih dalam 1800 detik (30 menit), THEN THE Bot SHALL menghentikan eksekusi
4. WHEN sesi selesai (berhasil maupun gagal), THE Bot SHALL memastikan semua instance browser dari sesi tersebut ditutup dengan benar untuk mencegah kebocoran memori
5. WHEN bot dihentikan oleh pengguna menggunakan Ctrl+C, THE Bot SHALL menyelesaikan sesi yang sedang berjalan dengan aman, menyimpan semua data yang sudah dikumpulkan, dan menampilkan ringkasan yang mencakup jumlah sesi berhasil, jumlah sesi gagal, dan total data yang berhasil dikumpulkan sebelum keluar

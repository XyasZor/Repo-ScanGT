# Repo-ScanGT

**Genetic Tools (GT)** membantu pengguna menilai sebuah repository sebelum memasang atau menjalankannya. GT menganalisis isi repo secara statis dan heuristik, lalu menghasilkan persentase bahaya, tingkat risiko, dan daftar temuan pola mencurigakan. Dan juga pemindai keamanan repository berbasis terminal.

Tempel URL repo (GitHub, GitLab, Bitbucket, Codeberg), tekan ENTER, dan dalam hitungan detik kamu mendapat persentase bahaya, analisa risiko, serta rincian isi repo. Cepat, ringan, dan tanpa dependensi eksternal.

> Hasil pemindaian hanyalah indikator risiko, bukan vonis mutlak. Tetap tinjau secara manual.




## Cara Pasang

Untuk Termux, Ubuntu, dan Ubuntu WSL klik ini: [INSTALL.md](INSTALL.md)




## Penjelasan 

Sebelum menjalankan perintah step-by-step, pastikan:

- Tidak ada folder atau file dengan nama yang sama di lokasi tempat kamu menjalankan `git clone`. Kalau ada, ganti namanya dulu, kalau tidak proses clone akan gagal.
- **Termux** adalah versi terbaru dari **F-Droid**, bukan dari Play Store.
- **Windows** sudah memakai **Ubuntu WSL** dan bisa dibuka dari Start Menu.
- **Ubuntu** punya akses `sudo`.
- Python 3.8 atau lebih baru dan Git sudah terpasang (langkahnya ada di INSTALL.md).
- Koneksi internet stabil.
- Terminal berukuran minimal 50x16 dan mendukung warna.

## Format Input yang Didukung

- URL repo: `https://github.com/owner/repo`
- Singkat: `owner/repo` (dianggap GitHub)
- GitLab, Bitbucket, Codeberg, dan Git SSH (`git@github.com:owner/repo.git`)
- Arsip langsung (`.zip`, `.tar.gz`)
- Folder lokal

## Apa yang Dipindai

- Kredensial yang bocor (token, API key, private key)
- Eksekusi kode dinamis dan perintah shell
- Obfuscation dan payload yang disamarkan
- Jaringan dan exfiltrasi data (webhook, IP mentah, reverse shell, miner)
- Persistensi dan perubahan sistem
- Pencurian data dan pengawasan (browser, wallet, keylogger)
- Dependensi, hook instalasi, typosquatting, dan workflow CI
- Berkas berbahaya (biner, berkas rahasia, symlink keluar repo)
- Reputasi repo (lisensi, usia, status arsip, fork)

## Cara Membaca Hasil

Persentase bahaya dibagi menjadi lima tingkat: **AMAN** (di bawah 10%), **RENDAH** (10-24%), **SEDANG** (25-49%), **TINGGI** (50-74%), dan **KRITIS** (75% ke atas). Temuan di folder tes dan dokumentasi diberi bobot lebih rendah. Laporan lengkap disimpan dalam format `.txt` dan `.json` di folder `~/.genetic-tools/reports/`.

## Batasan

- Analisa bersifat statis: kode repo yang dipindai tidak pernah dijalankan.
- GT bukan antivirus. Repo yang bersih dari pola belum tentu aman.
- Tool yang sah bisa memicu temuan (misalnya downloader yang memakai subprocess), dan pola baru bisa lolos. Tinjau konteks setiap temuan.
- Batas pemindaian: arsip maksimal 200 MB, 40.000 berkas, dan 300 detik. Jika terlampaui, hasil bisa tidak lengkap.
- Repo privat atau terkena batas permintaan GitHub butuh variabel `GITHUB_TOKEN`.

## Catatan Penting

Seluruh kode sengaja dibiarkan terbuka, tidak dienkripsi maupun disamarkan, karena dibuat sebagai referensi pembelajaran. Pemilik repo tidak mengklaim dan menolak disebut sebagai developer atau sejenisnya. Tool ini dibuat hanya demi efektivitas memeriksa keamanan sebuah repository GitHub dan sejenisnya sebelum digunakan.

Jangan lupa beri bintang (star) sebagai pengingat: memakai repo sembarangan bisa mengundang hal-hal yang tidak diinginkan.

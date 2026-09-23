# Convert.id — Universal All-in-One File Conversion Engine & Ecosystem

```text
   ______                                __     _     __
  / ____/___  ____ _   _____  _____/ /_   (_)___/ /
 / /   / __ \/ __ \ | / / _ \/ ___/ __/  / / __  / 
/ /___/ /_/ / / / / |/ /  __/ /  / /_   / / /_/ /  
\____/\____/_/ /_/|___/\___/_/   \__/  /_/\__,_/   
```

> **Universal cross-platform conversion engine with an all-in-one installer, 20 unexpected professional-grade superpowers, and a bespoke monochromatic developer workbench.**

---

## ⚡ 1-Line Universal Installers

Install and set up everything (including automated dependency doctor & portable binaries) directly from your terminal:

### 🪟 Windows (Pilih salah satu)

**Jika menggunakan Command Prompt (CMD biasa seperti di screenshot):**
```cmd
powershell -c "iwr -useb https://raw.githubusercontent.com/muhmdathalla/convert.id/main/install.ps1 | iex"
```

**Jika menggunakan PowerShell:**
```powershell
iwr -useb https://raw.githubusercontent.com/muhmdathalla/convert.id/main/install.ps1 | iex
```

### 🍎 macOS & 🐧 Linux (Terminal)
Buka Terminal (Zsh/Bash) dan jalankan:
```bash
curl -fsSL https://raw.githubusercontent.com/muhmdathalla/convert.id/main/install.sh | bash
```

---

## 🖤 UI/UX Philosophy: Monochromatic & Anti-AI

Convert.id menolak desain template AI generik (tanpa gradient ungu pastel murahan, tanpa card bulat raksasa yang boros ruang, tanpa animasi mengambang yang lambat). 

Convert.id mengadopsi estetika **High-Density Monochromatic Tactical Workbench**:
- **Strict Monochrome Palette**: `#09090b` Deep Obsidian, `#18181b` Charcoal, `#27272a` Subtle borders, `#fafafa` Pure white contrast.
- **Developer-Grade Typography**: JetBrains Mono & tabular numbers untuk presisi byte dan metadata.
- **Keyboard-First Experience**: `Ctrl+Enter` / `Cmd+Enter` instant conversion, drag-and-drop tactical crosshair canvas.
- **100% Offline Local Engine**: Tidak ada data yang dikirim ke server cloud pihak ketiga. Data Anda sepenuhnya aman di perangkat Anda.

Jalankan Web Workbench lokal kapan saja dengan:
```bash
convert web
```

---

## 🚀 20 Fitur Profesional & Anti-Mainstream (Power Features)

Convert.id tidak hanya mengonversi format biasa (PNG, JPG, MP4, PDF), tetapi juga menghadirkan **20 fitur tingkat lanjut** yang tidak disangka-sangka oleh pengguna:

1. **Target Size Budget Compressor (`--target-size`)**:
   Memaksa ukuran file hasil konversi persis di bawah batas target (misal: `24.5MB` untuk Discord/Email atau `200KB` untuk portal CPNS/instansi pemerintah) menggunakan adaptive 2-pass bitrate & quality calculation.
   ```bash
   convert video.mp4 --target-size 24MB
   convert photo.jpg photo.webp --target-size 180KB
   ```

2. **Raster to Clean Vector Auto-Tracer (PNG/JPG ➔ True SVG)**:
   Bukan sekadar membungkus bitmap ke dalam tag `<image>`, melainkan kalkulasi kontur kurva Bezier sebenarnya (*vectorization/tracing*) untuk logo dan sketsa.
   ```bash
   convert logo.png logo.svg --vector
   ```

3. **Forensic EXIF & Metadata Phantom Stripper**:
   Membersihkan 100% jejak privasi digital: koordinat GPS, serial number kamera, riwayat software editing, dan embedded thumbnail cache. Aktif secara default!
   ```bash
   convert private_photo.jfif cleaned.png --strip-exif
   ```

4. **Steganography Secret Vault (Anti-Censorship)**:
   Menyisipkan file rahasia atau pesan terenkripsi AES ke dalam pixel gambar tanpa merusak kualitas visual, lengkap dengan sandi pengaman.
   ```bash
   # Sembunyikan file rahasia
   convert carrier.png --stego-hide confidential.pdf --password "KunciRahasia99"
   
   # Ekstrak kembali
   convert carrier_stego.png --stego-extract --password "KunciRahasia99"
   ```

5. **Smart Local Background Cutout**:
   Memotong subjek objek dan menghapus latar belakang secara otomatis langsung di perangkat lokal (100% offline tanpa cloud API).
   ```bash
   convert product.jpg product.png --remove-bg
   ```

6. **PDF Fortress (Unlock, Auto-Redact & Compress)**:
   Membuka proteksi password izin cetak/salin, melakukan auto-redact sensor data sensitif (NIK 16 digit, Kartu Kredit, Email) secara otomatis dari seluruh halaman PDF, dan mengompres stream halaman.
   ```bash
   convert scanned.pdf clean.pdf --auto-redact --password "UserPass123"
   ```

7. **Universal Data Polyglot (JSON ↔ YAML ↔ TOML ↔ XML ↔ CSV ↔ SQL DDL/Inserts)**:
   Konversi dua arah untuk semua format data, termasuk konversi instan Excel/CSV langsung menjadi skrip `CREATE TABLE` dan `INSERT INTO` SQL siap pakai.
   ```bash
   convert dataset.csv schema.sql
   convert config.json config.yaml
   ```

8. **Silence & Dead-Air Clipper (Video/Audio)**:
   Mendeteksi bagian hening/diam pada rekaman podcast, zoom meeting, atau tutorial, lalu memotong jeda kosong secara cerdas.
   ```bash
   convert podcast.mp3 podcast_trimmed.mp3 --strip-silence
   ```

9. **Game Spritesheet Matrix Synthesizer**:
   Mengubah klip video pendek atau GIF animasi menjadi 2D game spritesheet atlas teroptimasi untuk web developer & game programmer.
   ```bash
   convert explosion.mp4 spritesheet.png --spritesheet
   ```

10. **Code Asset Generator (SVG ➔ React TSX / Vue / Flutter)**:
    Mengubah file vektor SVG langsung menjadi source code komponen React TypeScript (TSX), Vue 3 SFC, atau Flutter CustomPainter path.
    ```bash
    convert icon.svg IconComponent.tsx
    convert icon.svg IconComponent.vue
    convert icon.svg IconComponent.dart
    ```

11. **Audio Master & LUFS Broadcast Normalizer**:
    Menyesuaikan volume audio ke standar industri streaming modern (EBU R128 / -14 LUFS Spotify, YouTube, Apple Music) tanpa distorsi clipping.
    ```bash
    convert track.wav track_mastered.mp3 --normalize-lufs
    ```

12. **Auto-Pilot Hot-Folder Daemon (`convert watch`)**:
    Menjalankan background service yang memantau folder khusus; file apa pun yang dijatuhkan langsung dikonversi otomatis sesuai format target dan dipindah ke folder output.
    ```bash
    convert watch ~/Downloads/Incoming --to webp --out ~/Downloads/Converted
    ```

13. **AirDrop-Style Local Offline Transfer Capsule (`convert share`)**:
    Mengubah file hasil konversi menjadi server transfer lokal instan dengan QR Code di terminal; ponsel atau laptop lain di Wi-Fi yang sama cukup scan QR untuk mengunduh instan lewat LAN.
    ```bash
    convert share export.mp4
    ```

14. **Visual Pixel & Tabular Diff Inspector (`convert diff`)**:
    Mendeteksi dan menyorot perbedaan pixel antara dua gambar, atau perbedaan baris/kolom antara dua file CSV/Excel.
    ```bash
    convert diff before.png after.png
    convert diff jan_data.csv feb_data.csv
    ```

15. **Smart Container Repair & Truncated Media Fixer**:
    Memperbaiki file MP4 yang gagal diputar karena `moov atom` di akhir file rusak (akibat rekaman OBS/kamera putus di tengah jalan).
    ```bash
    convert corrupted.mp4 repaired.mp4 --repair
    ```

16. **Palette-Optimized High-Res GIF Loops**:
    Membuat animasi GIF dari klip video dengan generator palet 2-pass adaptif lanczos tanpa bintik-bintik kasar (*dithered bayer*).
    ```bash
    convert clip.mp4 animation.gif
    ```

17. **Archive Chameleon (On-the-Fly Streaming Repacker)**:
    Mengubah format arsip (misal `.tar.gz` ke `.zip`) secara in-memory streaming tanpa perlu mengekstrak ke hard disk terlebih dahulu.
    ```bash
    convert package.tar.gz package.zip
    ```

18. **E-Book Factory (Markdown/TXT ➔ EPUB 3)**:
    Mengubah kumpulan tulisan catatan Markdown langsung menjadi format e-book EPUB valid dengan metadata chapter rapi.
    ```bash
    convert notes.md mybook.epub
    ```

19. **Self-Healing Binary Doctor (`convert doctor`)**:
    Mendeteksi ketersediaan runtime eksternal (FFmpeg, Poppler, OpenCV) dan menyediakan fitur auto-download portable binary dalam 1 perintah.
    ```bash
    convert doctor --fix
    ```

20. **Format Autodiscovery & Magic-Byte Sniffer**:
    Mampu mengenali file `.jfif` yang salah dinamai `.jpg`, atau file WebP tanpa ekstensi, langsung menganalisis tanda tangan byte aslinya dan mengonversinya secara presisi.

---

## 📂 Matriks Format yang Didukung

| Kategori | Format Input & Output |
| :--- | :--- |
| **Gambar** | `PNG`, `JPG`, `JPEG`, `JFIF`, `WEBP`, `AVIF`, `SVG`, `BMP`, `TIFF`, `ICO`, `GIF`, `TGA`, `DDS` |
| **Video** | `MP4`, `MKV`, `AVI`, `MOV`, `WEBM`, `FLV`, `WMV`, `TS`, `M4V`, `GIF` |
| **Audio** | `MP3`, `WAV`, `FLAC`, `AAC`, `OGG`, `M4A`, `OPUS`, `WMA`, `AIFF` |
| **Dokumen** | `PDF`, `DOCX`, `TXT`, `MD`, `HTML`, `EPUB`, `RTF` |
| **Data & Tabular** | `JSON`, `YAML`, `TOML`, `XML`, `CSV`, `TSV`, `SQL DDL/Inserts`, `XLSX`, `PARQUET` |
| **Arsip** | `ZIP`, `TAR`, `GZ`, `TAR.GZ`, `TGZ`, `BZ2`, `TAR.BZ2`, `XZ`, `TAR.XZ`, `7Z` |
| **Code** | `SVG ➔ React TSX`, `SVG ➔ Vue SFC`, `SVG ➔ Flutter Dart` |

---

## 💻 Penggunaan Cepat (CLI)

```bash
# Konversi gambar mainstream & anti-mainstream
convert photo.jfif photo.png
convert photo.png photo.webp
convert graphic.png graphic.svg --vector

# Video & Audio
convert footage.mkv footage.mp4
convert podcast.wav podcast.mp3 --normalize-lufs
convert clip.mp4 animation.gif

# Dokumen & Data
convert document.docx notes.md
convert scanned.pdf output.pdf --auto-redact
convert data.csv database.sql

# Menjalankan Web UI Monokrom
convert web
```

---

## 🛠️ Pengembangan Lokal

```bash
git clone https://github.com/muhmdathalla/convert.id.git
cd convert.id
python -m pip install -e .
pytest tests/  # atau python tests/test_image.py
```

---

## 📜 Lisensi

Didistribusikan di bawah lisensi MIT. Dibuat dengan bangga oleh [muhmdathalla](https://github.com/muhmdathalla).

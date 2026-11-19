# Monitoring Kelembapan Tanah Berbasis IoT dan Evaluasi Protokol MQTT vs HTTP

Tugas Besar UTS - Internet of Things: Protokol, Platform, dan AI (Kelompok Ellembap).

Sistem terdiri dari dua bagian:

- **Bagian A** - ESP32 + sensor FC-28 mengirim nilai ADC kelembapan tanah ke
  ThingSpeak setiap 30 detik. Data direkam 7 hari kalender (8-14 November 2026),
  sesi uji sekitar 2 jam per hari sesuai arahan dosen.
- **Bagian B** - Eksperimen HTTP POST vs MQTT (QoS 0 dan QoS 1) pada payload
  +-20 byte dan +-500 byte (S1-S6, masing-masing 100 pesan, jeda 2 detik) di Wokwi.

## Tautan

- ThingSpeak: Channel ID 3570142 (privat; Read API Key diberikan ke dosen secara privat).
- Credential (SSID, kata sandi Wi-Fi, Write API Key) tidak disertakan di repositori.

## Data

| Berkas | Isi |
| --- | --- |
| `dataset_7hari.csv` | Dataset gabungan 8-14 November 2026 (1.717 entry, zona waktu +07:00) |
| `label_log.csv` | 102 kejadian berlabel (34 per kelas: Normal, Watered, Sun-Exposed) |
| `day_4_cleaned_1120_1320.csv` | Data percobaan ulang 11 November, 11:20-13:20 WIB (222 entry) |
| `exp_S1.csv` ... `exp_S6.csv` | Log per pesan eksperimen S1-S6 |

Catatan pengolahan data:

- CSV dikonversi dari ekspor xlsx ThingSpeak. Baris judul rekap dihapus dan header
  dijadikan baris pertama; nilai data tidak diubah.
- `day_4_cleaned_1120_1320.csv` memakai zona waktu UTC (04:20 UTC = 11:20 WIB).
- `label_log.csv` disusun dari jadwal SOP (siklus 24 menit: Normal, Watered 20 ml,
  Sun-Exposed masing-masing 8 menit) berdasarkan jam mulai tiap sesi, bukan dari
  catatan manual per kejadian. Batas antar fase dapat bergeser beberapa menit.
- Kejadian terakhir (L102) terpotong karena data channel berakhir pukul 14:08:42.
- Foto bukti kejadian tersedia sebagian (lihat Lampiran 1 dan 4 di laporan).

## Eksperimen protokol (Bagian B)

| Skenario | Protokol | Payload |
| --- | --- | --- |
| S1 | HTTP POST | +-20 byte |
| S2 | HTTP POST | +-500 byte |
| S3 | MQTT QoS 0 | +-20 byte |
| S4 | MQTT QoS 0 | +-500 byte |
| S5 | MQTT QoS 1 | +-20 byte |
| S6 | MQTT QoS 1 | +-500 byte |

Tanpa TLS (HTTP port 80, MQTT port 1883). RTT diukur di perangkat yang sama
(HTTP: request sampai response; MQTT: publish sampai pesan kembali dari broker pada
topik yang sama). Pesan yang tidak kembali dalam 5 detik dianggap hilang. Metrik:
RTT (mean, median, simpangan baku, P95), PDR, dan overhead header Layer 7.

## Reproduksi analisis

Letakkan `analisis.py`, `dataset_7hari.csv`, `label_log.csv`, dan `exp_S1.csv` ... `exp_S6.csv`
di satu folder, lalu jalankan:

```
pip install pandas numpy matplotlib
python analisis.py --exp-dir . --dataset dataset_7hari.csv --labels label_log.csv
```

Skrip menulis tabel CSV dan boxplot RTT ke folder `output_analisis/`. Entry percobaan awal
11 November (di luar 11:20-13:20 WIB) dibuang otomatis; gunakan `--keep-all` untuk memakai
seluruh entry channel. Semua angka dihitung dari berkas CSV, tidak ada nilai hasil yang ditulis manual.

## Penggunaan AI

Penggunaan AI dicatat pada Tabel D.1 di laporan dan pada berkas log penggunaan AI.

# Sistem Monitoring Kelembapan Tanah Berbasis ESP32 dan Evaluasi Protokol HTTP vs MQTT

Repositori dokumentasi, kode program (*firmware*), dataset pengujian, dan skrip analisis untuk Tugas Besar Internet of Things (IoT).

## Anggota Kelompok
* **Stefani**
* **Ali**
* **Ghulam**

## Spesifikasi Sistem
* **Mikrokontroler & Sensor:** ESP32 DevKit + Sensor Kelembapan Tanah FC-28 (Pin GPIO 34, ADC 12-bit)
* **Platform Cloud (Bagian A):** ThingSpeak (Channel ID: `3570142`)
* **Simulasi & Uji Protokol (Bagian B):** Wokwi Simulator (Skenario `S1`–`S6` menggunakan HTTP POST pada `httpbin.org` dan MQTT QoS 0/1 pada `broker.hivemq.com`)

## Daftar Berkas Repositori
* `esp.txt` — Kode program ESP32 pengiriman data ke ThingSpeak
* `wokwi.txt` — Kode program simulasi Wokwi skenario S1–S6
* `DATA CSV DAY 1.csv` – `day 7(1).xlsx` & `label_log.csv` — Dataset monitoring 7 hari dan log kejadian perlakuan
* `S1` – `S6 (.xlsx)` — Log hasil pengujian latensi (RTT) dan PDR tiap skenario
* `foto_normal_01.jpg`, `foto_watered_01.jpg`, `foto_sun_01.jpg` — Dokumentasi fisik kondisi perlakuan media tanam

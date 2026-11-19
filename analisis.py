#!/usr/bin/env python3
"""
Skrip Analisis Tugas Besar IoT (HTTP vs MQTT & Dataset Sensor 7 Hari)
Semua metrik dihitung dari berkas CSV mentah; tidak ada angka hasil yang ditulis manual.

Cara menjalankan (dari root repositori):
    pip install pandas numpy matplotlib
    python scripts/analisis.py --exp-dir data/eksperimen \
        --dataset data/dataset_7hari/dataset_7hari.csv \
        --labels data/dataset_7hari/label_log.csv --out-dir output_analisis
"""

import argparse
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

TZ = "Asia/Jakarta"

# Panjang header Layer 7 per skenario (byte), berdasarkan RFC 7230 (HTTP/1.1)
# dan OASIS MQTT v3.1.1.
HEADER_L7_BYTES = {"S1": 196, "S2": 197, "S3": 36, "S4": 37, "S5": 38, "S6": 39}

# Percobaan awal 11 November (sensor belum di tanah) dibuang; hanya data
# 11:20-13:20 WIB pada tanggal tersebut yang dipakai (lihat laporan A.9/C.3).
TANGGAL_PERCOBAAN_ULANG = "2026-11-11"
JAM_MULAI_VALID = "11:20:00"
JAM_SELESAI_VALID = "13:20:00"

BATAS_CELAH_DETIK = 90          # selisih antar-entry di atas ini dianggap celah
BATAS_ANTAR_SESI_DETIK = 1800   # selisih di atas ini = jeda antar sesi uji, bukan celah


def analisis_eksperimen_protokol(exp_dir, out_dir):
    """Bagian 1: metrik PDR, RTT (hanya SUCCESS), overhead Layer 7, dan boxplot RTT."""
    skenario_list = ["S1", "S2", "S3", "S4", "S5", "S6"]
    hasil_rows, rtt_per_skenario = [], []

    for sken in skenario_list:
        file_path = os.path.join(exp_dir, f"exp_{sken}.csv")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Berkas log eksperimen tidak ditemukan: {file_path}")

        df = pd.read_csv(file_path)
        total_sent = len(df)
        df_success = df[df["status"].astype(str).str.strip().str.upper() == "SUCCESS"].copy()
        total_recv = len(df_success)
        pdr_pct = (total_recv / total_sent * 100.0) if total_sent > 0 else 0.0

        rtt_vals = pd.to_numeric(df_success["rtt_ms"], errors="coerce").dropna().to_numpy()
        if len(rtt_vals) > 0:
            rtt_mean = float(np.mean(rtt_vals))
            rtt_median = float(np.median(rtt_vals))
            rtt_sd = float(np.std(rtt_vals, ddof=1)) if len(rtt_vals) > 1 else 0.0
            rtt_p95 = float(np.percentile(rtt_vals, 95, method="linear"))
        else:
            rtt_mean = rtt_median = rtt_sd = rtt_p95 = np.nan

        payload_vals = pd.to_numeric(df_success["payload_byte"], errors="coerce").dropna()
        mean_payload = float(payload_vals.mean()) if len(payload_vals) > 0 else 0.0
        header_byte = HEADER_L7_BYTES[sken]
        total_l7 = header_byte + mean_payload
        overhead_ratio_pct = (header_byte / total_l7 * 100.0) if total_l7 > 0 else 0.0

        hasil_rows.append({
            "Skenario": sken, "Sent": total_sent, "Recv": total_recv,
            "PDR_pct": round(pdr_pct, 2),
            "Mean_RTT_ms": round(rtt_mean, 2), "Median_RTT_ms": round(rtt_median, 2),
            "SD_RTT_ms": round(rtt_sd, 2), "P95_RTT_ms": round(rtt_p95, 2),
            "Header_L7_byte": header_byte, "Mean_Payload_byte": round(mean_payload, 2),
            "Overhead_Ratio_pct": round(overhead_ratio_pct, 2),
        })
        rtt_per_skenario.append(rtt_vals)

    df_hasil = pd.DataFrame(hasil_rows)
    df_hasil.to_csv(os.path.join(out_dir, "hasil_eksperimen_protokol.csv"), index=False)

    plt.figure(figsize=(10, 5.5), dpi=300)
    try:
        box = plt.boxplot(rtt_per_skenario, tick_labels=skenario_list, patch_artist=True,
                          showmeans=True,
                          meanprops=dict(marker="D", markeredgecolor="black", markerfacecolor="gold", markersize=6),
                          medianprops=dict(color="darkred", linewidth=1.8))
    except TypeError:  # matplotlib < 3.9
        box = plt.boxplot(rtt_per_skenario, labels=skenario_list, patch_artist=True,
                          showmeans=True,
                          meanprops=dict(marker="D", markeredgecolor="black", markerfacecolor="gold", markersize=6),
                          medianprops=dict(color="darkred", linewidth=1.8))
    for patch, color in zip(box["boxes"], ["#e06666", "#e06666", "#6fa8dc", "#6fa8dc", "#93c47d", "#93c47d"]):
        patch.set_facecolor(color)
        patch.set_alpha(0.85)
    plt.title("Distribusi Round-Trip Time (RTT) Enam Skenario Pengujian (S1–S6)", fontweight="bold")
    plt.xlabel("Skenario Pengujian (Protokol, QoS, dan Ukuran Payload)")
    plt.ylabel("Round-Trip Time / RTT (ms)")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "boxplot_rtt_skenario.png"))
    plt.close()
    return df_hasil


def analisis_dataset_sensor(dataset_path, label_path, out_dir, buang_percobaan_awal=True):
    """Bagian 2: kelengkapan, celah waktu, nilai jenuh 4095, statistik field1, rata-rata per kelas."""
    for p, nama in ((dataset_path, "dataset sensor"), (label_path, "log label")):
        if not os.path.isfile(p):
            raise FileNotFoundError(f"Berkas {nama} tidak ditemukan: {p}")

    df = pd.read_csv(dataset_path)
    df["created_at_dt"] = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert(TZ)
    df["field1_num"] = pd.to_numeric(df["field1"], errors="coerce")
    df = df.sort_values("created_at_dt").reset_index(drop=True)
    jumlah_entry_channel = len(df)

    jumlah_dibuang = 0
    if buang_percobaan_awal:
        a = pd.Timestamp(f"{TANGGAL_PERCOBAAN_ULANG} {JAM_MULAI_VALID}", tz=TZ)
        b = pd.Timestamp(f"{TANGGAL_PERCOBAAN_ULANG} {JAM_SELESAI_VALID}", tz=TZ)
        hari = df["created_at_dt"].dt.strftime("%Y-%m-%d") == TANGGAL_PERCOBAAN_ULANG
        buang = hari & ((df["created_at_dt"] < a) | (df["created_at_dt"] > b))
        jumlah_dibuang = int(buang.sum())
        df = df[~buang].reset_index(drop=True)

    jumlah_entry = len(df)
    df["delta_detik"] = df["created_at_dt"].diff().dt.total_seconds()
    interval_median = float(df["delta_detik"].dropna().median())

    # Celah = jeda di dalam sesi uji (90 s < selisih <= 1800 s); jeda lebih panjang = antar sesi.
    celah_mask = (df["delta_detik"] > BATAS_CELAH_DETIK) & (df["delta_detik"] <= BATAS_ANTAR_SESI_DETIK)
    antar_mask = df["delta_detik"] > BATAS_ANTAR_SESI_DETIK
    df_celah = df[celah_mask]
    jumlah_celah = len(df_celah)
    jumlah_antar_sesi = int(antar_mask.sum())

    pd.DataFrame({
        "waktu_sebelum_WIB": df.loc[df_celah.index - 1, "created_at_dt"].astype(str).values,
        "waktu_sesudah_WIB": df_celah["created_at_dt"].astype(str).values,
        "durasi_celah_detik": df_celah["delta_detik"].values,
    }).to_csv(os.path.join(out_dir, "hasil_celah_waktu.csv"), index=False)

    jumlah_4095 = int((df["field1_num"] == 4095).sum())
    valid_all = df["field1_num"].dropna()
    valid_no = df.loc[df["field1_num"] != 4095, "field1_num"].dropna()

    def baris(nama, s, n4095):
        return {"Subset_Data": nama, "Count": int(len(s)), "Min": float(s.min()), "Max": float(s.max()),
                "Mean": round(float(s.mean()), 2), "SD_sampel": round(float(s.std(ddof=1)), 2),
                "Interval_Median_detik": round(interval_median, 2),
                "Entry_Channel_Awal": jumlah_entry_channel, "Entry_Dibuang_Percobaan_Awal": jumlah_dibuang,
                "Jumlah_Celah_dalam_sesi": jumlah_celah, "Jumlah_Jeda_antar_sesi": jumlah_antar_sesi,
                "Jumlah_Nilai_4095": n4095}

    df_stat = pd.DataFrame([baris("Dataset analisis (semua entry)", valid_all, jumlah_4095),
                            baris("Tanpa nilai jenuh (field1 != 4095)", valid_no, 0)])
    df_stat.to_csv(os.path.join(out_dir, "hasil_statistik_dataset.csv"), index=False)

    # Rata-rata field1 per kelas; jendela kejadian [mulai, selesai) agar entry di batas
    # dua kejadian tidak terhitung dua kali. Nilai 4095 dikecualikan.
    lab = pd.read_csv(label_path)
    lab["mulai_dt"] = pd.to_datetime(lab["mulai"], utc=True).dt.tz_convert(TZ)
    lab["selesai_dt"] = pd.to_datetime(lab["selesai"], utc=True).dt.tz_convert(TZ)
    bersih = df[df["field1_num"] != 4095]

    potongan = []
    for _, r in lab.iterrows():
        m = (bersih["created_at_dt"] >= r["mulai_dt"]) & (bersih["created_at_dt"] < r["selesai_dt"])
        s = bersih.loc[m, ["field1_num"]].copy()
        s["kelas"] = str(r["kelas"]).strip()
        s["label_id"] = r["label_id"]
        potongan.append(s)
    df_lab = pd.concat(potongan, ignore_index=True)
    df_kelas = (df_lab.groupby("kelas", as_index=False)
                .agg(Jumlah_Kejadian=("label_id", "nunique"), Jumlah_Entry_Valid=("field1_num", "count"),
                     Min_ADC=("field1_num", "min"), Max_ADC=("field1_num", "max"),
                     Mean_ADC=("field1_num", "mean"),
                     SD_ADC=("field1_num", lambda x: float(x.std(ddof=1)) if len(x) > 1 else 0.0)))
    df_kelas["Mean_ADC"] = df_kelas["Mean_ADC"].round(2)
    df_kelas["SD_ADC"] = df_kelas["SD_ADC"].round(2)
    df_kelas.to_csv(os.path.join(out_dir, "hasil_perbandingan_kelas.csv"), index=False)
    return df_stat, df_kelas, df_celah


def main():
    ap = argparse.ArgumentParser(description="Analisis eksperimen protokol (S1-S6) dan dataset sensor 7 hari.")
    ap.add_argument("--exp-dir", default="data/eksperimen")
    ap.add_argument("--dataset", default="data/dataset_7hari/dataset_7hari.csv")
    ap.add_argument("--labels", default="data/dataset_7hari/label_log.csv")
    ap.add_argument("--out-dir", default="output_analisis")
    ap.add_argument("--keep-all", action="store_true",
                    help="Jangan buang percobaan awal 11 November (pakai seluruh entry channel)")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 50)

    print("=" * 70)
    print("BAGIAN 1: EKSPERIMEN PROTOKOL HTTP VS MQTT (S1–S6)")
    print("=" * 70)
    print(analisis_eksperimen_protokol(args.exp_dir, args.out_dir).to_string(index=False))

    df_stat, df_kelas, _ = analisis_dataset_sensor(args.dataset, args.labels, args.out_dir,
                                                   buang_percobaan_awal=not args.keep_all)
    print("\n" + "=" * 70)
    print("BAGIAN 2A: STATISTIK DATASET SENSOR 7 HARI")
    print("=" * 70)
    print(df_stat.to_string(index=False))
    print("\n" + "=" * 70)
    print("BAGIAN 2B: RATA-RATA FIELD1 PER KELAS (TANPA NILAI 4095)")
    print("=" * 70)
    print(df_kelas.to_string(index=False))
    print(f"\nSelesai. Hasil tersimpan di folder: {args.out_dir}/")


if __name__ == "__main__":
    main()

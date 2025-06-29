import pandas as pd
import numpy as np
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt
import sys
import os           

PRE_CSV = "pre_dataset/imu_log_pre1.csv"
POST_CSV = "post_dataset/imu_log_post3.csv"
AXIS = "raw_z"
RANGE_G = 2
ADC_SCALE = 32768 / (2 * RANGE_G)
WINDOW_SECONDS = 1

def load_and_process(csv_path):
    if not os.path.exists(csv_path):
        print(f"ERROR: File {csv_path} not found.")
        sys.exit(1)

    df = pd.read_csv(csv_path)
    time_col = 'elapsed_sec' if 'elapsed_sec' in df.columns else 'timestamp'
    timestamps = df[time_col].values
    signal_raw = df[AXIS].values
    signal = signal_raw / ADC_SCALE  

    time_diffs = np.diff(timestamps)
    avg_dt = np.mean(time_diffs)
    fs = 1.0 / avg_dt

    n = len(signal)
    signal_centered = signal - np.mean(signal)
    fft_vals = rfft(signal_centered)
    freqs = rfftfreq(n, d=avg_dt)
    magnitudes = np.abs(fft_vals)

    rms_raw = np.sqrt(np.mean(signal**2))
    rms_centered = np.sqrt(np.mean(signal_centered**2))
    ptp = np.ptp(signal)
    spectral_energy = np.sum(magnitudes**2)

    window_size = int(fs * WINDOW_SECONDS)
    rms_vals, ptp_vals, energy_vals = [], [], []
    for i in range(0, len(signal) - window_size, window_size):
        window = signal[i:i+window_size]
        centered = window - np.mean(window)
        rms_vals.append(np.sqrt(np.mean(centered**2)))
        ptp_vals.append(np.ptp(centered))
        window_fft = np.abs(rfft(centered))
        energy_vals.append(np.sum(window_fft**2))

    return {
        'signal': signal,
        'freqs': freqs,
        'magnitudes': magnitudes,
        'sampling_rate': fs,

        'rms_raw': rms_raw,
        'rms_centered': rms_centered,

        'rms_window_mean': np.mean(rms_vals),
        'rms_window_std': np.std(rms_vals),

        'ptp_window_mean': np.mean(ptp_vals),
        'ptp_window_std': np.std(ptp_vals),

        'energy_window_mean': np.mean(energy_vals),
        'energy_window_std': np.std(energy_vals),

        'energy_total': spectral_energy
    }

def pct_reduction(pre_val, post_val):
    return 100 * (pre_val - post_val) / pre_val if pre_val != 0 else 0

print("Processing PRE dataset...")
pre = load_and_process(PRE_CSV)
print("Processing POST dataset...")
post = load_and_process(POST_CSV)

print("\n=== VIBRATION ANALYSIS COMPARISON ===")
print(f"Sampling Rate: {pre['sampling_rate']:.2f} Hz")

print(f"\n--- RMS Amplitude (Raw) ---")
print(f"Pre : {pre['rms_raw']:.4f} g")
print(f"Post: {post['rms_raw']:.4f} g")
print(f"↓ Reduction: {pct_reduction(pre['rms_raw'], post['rms_raw']):.2f}%")

print(f"\n--- RMS Amplitude (Mean-Centered) ---")
print(f"Pre : {pre['rms_centered']:.4f} g")
print(f"Post: {post['rms_centered']:.4f} g")
print(f"↓ Reduction: {pct_reduction(pre['rms_centered'], post['rms_centered']):.2f}%")

print(f"\n--- Windowed RMS (1s, Mean-Centered) ---")
print(f"Pre : {pre['rms_window_mean']:.4f} ± {pre['rms_window_std']:.4f} g")
print(f"Post: {post['rms_window_mean']:.4f} ± {post['rms_window_std']:.4f} g")
print(f"↓ Reduction: {pct_reduction(pre['rms_window_mean'], post['rms_window_mean']):.2f}%")

print(f"\n--- Windowed Peak-to-Peak Amplitude ---")
print(f"Pre : {pre['ptp_window_mean']:.4f} ± {pre['ptp_window_std']:.4f} g")
print(f"Post: {post['ptp_window_mean']:.4f} ± {post['ptp_window_std']:.4f} g")
print(f"↓ Reduction: {pct_reduction(pre['ptp_window_mean'], post['ptp_window_mean']):.2f}%")

print(f"\n--- Windowed Spectral Energy ---")
print(f"Pre : {pre['energy_window_mean']:.4f} ± {pre['energy_window_std']:.4f}")
print(f"Post: {post['energy_window_mean']:.4f} ± {post['energy_window_std']:.4f}")
print(f"↓ Reduction: {pct_reduction(pre['energy_window_mean'], post['energy_window_mean']):.2f}%")

print(f"\n--- Total Spectral Energy ---")
print(f"Pre : {pre['energy_total']:.2f}")
print(f"Post: {post['energy_total']:.2f}")
print(f"↓ Reduction: {pct_reduction(pre['energy_total'], post['energy_total']):.2f}%")


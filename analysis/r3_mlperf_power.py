"""Round 3, weak point "machine and income": energy per unit of work from MLPerf power runs.

Exploratory. Not part of the scheduler. Standard library only.

    python3 analysis/r3_mlperf_power.py            # downloads about 1.3 MB of public logs
    python3 analysis/r3_mlperf_power.py --offline  # prints the values stored below, no network

What it does: for the two MLPerf Inference v5.1 closed-division submissions that
carry a power measurement for whisper and for llama3.1-8b (both Lenovo, 8 x B200),
it reads the loadgen summary (samples/s, tokens/s), the loadgen detail log
(power_begin, power_end) and the power analyser samples (spl.txt, one line per
second, total watts of a 3-channel Yokogawa WT500), averages the watts inside the
test window and prints work per joule and per kWh.

Why v5.1: in the summary files of v6.0 (520 rows) and v6.1 (492 rows) the field
has_power is False for every row; v5.1 has 24 rows with has_power True, of which
one is whisper Offline and one is llama3.1-8b Offline.
"""
import re
import sys
import urllib.request
from datetime import datetime

BASE = ("https://raw.githubusercontent.com/mlcommons/inference_results_v5.1/main/"
        "closed/Lenovo/results/")
RUNS = {
    # label: (path, MLPerf ID, system)
    "whisper": ("SR680a_V3_B200SXMx8_TRT/whisper/Offline/performance/run_1/",
                "5.1-0061", "Lenovo ThinkSystem SR680a V3, 8 x NVIDIA B200-SXM-180GB, 2 x Xeon 8568Y+"),
    "llama3.1-8b": ("SR780a_V3_B200SXMx8_TRT/llama3.1-8b/Offline/performance/run_1/",
                    "5.1-0062", "Lenovo ThinkSystem SR780a V3, 8 x NVIDIA B200-SXM-180GB, 2 x Xeon 8568Y+"),
}
# Values this script printed on 2026-11-21 (used by --offline and by r3_income.py).
STORED = {
    "whisper": {"samples_s": 688.623, "tokens_s": 43698.6, "avg_w": 7636.49, "window_s": 623.678},
    "llama3.1-8b": {"samples_s": 1148.12, "tokens_s": 146960.0, "avg_w": 9436.05, "window_s": 640.383},
}
# MLPerf whisper data set: 1,633 samples (mlperf.conf), "approximately 10 hours"
# (speech2text README). 10 h / 1,633 = 22.05 s of audio per sample. APPROXIMATE.
WHISPER_SAMPLES = 1633
WHISPER_AUDIO_H = 10.0
FMT = "%m-%d-%Y %H:%M:%S.%f"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "generic-client"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def measure(path):
    summ = get(BASE + path + "mlperf_log_summary.txt")
    det = get(BASE + path + "mlperf_log_detail.txt")
    spl = get(BASE + path + "spl.txt")
    samples_s = float(re.search(r"Samples per second: ([\d.]+)", summ).group(1))
    tokens_s = float(re.search(r"Tokens per second: ([\d.]+)", summ).group(1))
    b = datetime.strptime(re.search(r'"power_begin", "value": "([^"]+)"', det).group(1), FMT)
    e = datetime.strptime(re.search(r'"power_end", "value": "([^"]+)"', det).group(1), FMT)
    watts = []
    for line in spl.splitlines():
        p = line.split(",")
        if len(p) > 3 and p[0] == "Time" and b <= datetime.strptime(p[1], FMT) <= e:
            watts.append(float(p[3]))
    return {"samples_s": samples_s, "tokens_s": tokens_s, "avg_w": sum(watts) / len(watts),
            "window_s": (e - b).total_seconds(), "n": len(watts), "min_w": min(watts), "max_w": max(watts)}


def derived(label, m):
    out = {"j_per_sample": m["avg_w"] / m["samples_s"],
           "tokens_per_j": m["tokens_s"] / m["avg_w"],
           "tokens_per_kwh": m["tokens_s"] / m["avg_w"] * 3.6e6,
           "samples_per_kwh": m["samples_s"] / m["avg_w"] * 3.6e6,
           "tokens_per_sample": m["tokens_s"] / m["samples_s"]}
    if label == "whisper":
        sec = WHISPER_AUDIO_H * 3600 / WHISPER_SAMPLES
        out["audio_s_per_sample"] = sec
        out["audio_h_per_kwh"] = out["samples_per_kwh"] * sec / 3600
        out["wh_per_audio_h"] = 1000 / out["audio_h_per_kwh"]
        out["realtime_factor"] = m["samples_s"] * sec
    return out


if __name__ == "__main__":
    offline = "--offline" in sys.argv
    for label, (path, mid, system) in RUNS.items():
        m = STORED[label] if offline else measure(path)
        d = derived(label, m)
        print(f"== {label}  MLPerf Inference v5.1 closed, ID {mid}")
        print(f"   system: {system}")
        print(f"   source folder: {BASE.replace('raw.githubusercontent.com/mlcommons/inference_results_v5.1/main', 'github.com/mlcommons/inference_results_v5.1/tree/main')}{path}")
        print(f"   loadgen: {m['samples_s']:.3f} samples/s, {m['tokens_s']:.1f} tokens/s "
              f"({d['tokens_per_sample']:.1f} tokens per sample)")
        extra = "" if offline else f", {m['n']} samples, min {m['min_w']:.0f} W, max {m['max_w']:.0f} W"
        print(f"   wall power, mean inside power_begin..power_end ({m['window_s']:.0f} s): "
              f"{m['avg_w']:.1f} W{extra}")
        print(f"   {d['j_per_sample']:.2f} J per sample; {d['tokens_per_j']:.3f} tokens per J; "
              f"{d['tokens_per_kwh']/1e6:.2f} million tokens per kWh; {d['samples_per_kwh']:.0f} samples per kWh")
        if label == "whisper":
            print(f"   with {d['audio_s_per_sample']:.2f} s audio per sample (10 h / 1,633, APPROXIMATE): "
                  f"{d['audio_h_per_kwh']:.0f} audio-hours per kWh = {d['wh_per_audio_h']:.3f} Wh per audio-hour; "
                  f"{d['realtime_factor']:.0f} x real time for the whole 8-GPU machine")
            hi = m["samples_s"] / m["avg_w"] * 3.6e6 * 30 / 3600
            print(f"   upper bound if every sample were 30 s: {hi:.0f} audio-hours per kWh = {1000/hi:.3f} Wh per audio-hour")
        print()
    print("Note: both machines draw 7.6 to 9.4 kW. 'Per kWh' is a 1 kW SLICE of such a machine, not a 1 kW machine.")

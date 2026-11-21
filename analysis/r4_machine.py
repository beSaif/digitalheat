"""Round 4: one coherent reference machine near 1 kW and its full installed cost.

Exploratory analysis, NOT the team's scheduler. Standard library only.

    python3 analysis/r4_machine.py
    python3 analysis/r4_machine.py --years 5 8 --sold 0.67 --operator-share 0.20

Reference machine (one box runs BOTH job types, same MLPerf system for both):
  2U single-socket server with 4 x NVIDIA RTX PRO 4500 Blackwell Server Edition (32 GB, 165 W max each).
  Throughput: MLPerf Inference v6.1, ID 6.1-0017, Cisco UCS X210 M8 X580P node, 4 x RTX PRO 4500 Blackwell,
  closed division, Offline scenario, loadgen mlperf_log_summary.txt:
    whisper (large-v3, fp16)      61.104 samples/s  (3,877.67 tokens/s)
    llama3.1-8b (fp4 weights)     9,518.66 output tokens/s (73.7905 samples/s)
  Cross-check: ID 6.1-0056, HPE ProLiant DL345 Gen12 (1 x EPYC 9375F), 4 x RTX PRO 4500 Server Edition,
    whisper Offline 58.0816 samples/s.
  No power was measured in v6.1. Wall power below is an ASSUMPTION built on sourced component maxima.

Everything is normalised to the case's server: 1 server = 1 kW of electricity = 1 / P_wall boxes of this
machine. Run hours, electricity and heat value come from baseline_sweep.simulate (unchanged, policy follow).
"""
import argparse
from baseline_sweep import load, simulate, PRICE, HEAT_VALUE

USD_CHF = 0.8392   # ECB reference rates 20 Nov 2026 (USD 1.0990, CHF 0.9223), sourced in round 1
EUR_CHF = 0.9223   # same ECB table
VAT_CH = 0.081     # ESTV normal rate 8.1 % (estv.admin.ch/en/vat-rates-switzerland), read 21 Nov 2026
VAT_DE = 0.19      # German VAT used by the German shop prices (assumption: standard rate)

# ---- throughput of one box (SOURCED, MLPerf v6.1 loadgen summaries) ----
WHISPER_SAMPLES_S = 61.104          # 6.1-0017 whisper Offline
WHISPER_SAMPLES_S_HPE = 58.0816     # 6.1-0056 whisper Offline (cross-check)
AUDIO_S_PER_SAMPLE = 22.05          # r3: "approximately 10 hours" / 1,633 samples (MLPerf speech2text README)
AUDIO_S_PER_SAMPLE_MAX = 30.0       # samples are zero-padded to 30 s: upper bound on audio per sample
LLAMA_TOK_S = 9518.66               # 6.1-0017 llama3.1-8b Offline, output tokens/s, fp4

# ---- wall power of one box, kW (ASSUMPTION built on SOURCED maxima) ----
GPU_MAX_W = 165.0                   # NVIDIA RTX PRO 4500 Blackwell Server Edition, "Max power consumption 165 W"
N_GPU = 4
CPU_TDP_W = 320.0                   # AMD EPYC 9375F default TDP 320 W (the CPU in the HPE MLPerf box)
POWER_CASES = {                     # (GPU share of max, CPU W, rest W, PSU efficiency)  all ASSUMPTION
    "low":     (0.85, 100.0, 60.0, 0.96),
    "central": (0.95, 180.0, 100.0, 0.95),
    "high":    (1.00, CPU_TDP_W, 150.0, 0.93),
}


def wall_kw(case):
    g, cpu, rest, eff = POWER_CASES[case]
    return (N_GPU * GPU_MAX_W * g + cpu + rest) / eff / 1000.0


# ---- prices of the work (r3 surviving scenario, SOURCED in r3, USD) ----
J1_USD_PER_AUDIO_H = {"low": 0.012, "central": 0.020, "high": 0.045}
J1_USD_LARGE_V3_BATCH = 0.0555      # Groq whisper-large-v3 batch (r3, sourced): the model MLPerf actually runs
J2_USD_PER_M_OUT = {"low": 0.04, "central": 0.16, "high": 0.77}   # central/high use 6:1 input ratio (ASSUMPTION)
MIX_J1 = 0.5                        # share of server-hours on J1 (ASSUMPTION, r3 default)

# ---- installed cost, CHF incl. 8.1 % Swiss VAT ----
# GPU card, per card:
CARD_CH_LOW = 4819.00               # shop.post.ch, "PNY Graphics Card RTX PRO 4500", passive, read 21 Nov 2026
CARD_CH_HIGH = 5641.95              # ldlc.com/fr-ch, "PNY NVIDIA RTX PRO 4500 Blackwell Edition serveur", 21 Nov 2026
CARD_DE_EUR_MIN = 4679.00           # hardwaredealz price comparison, alza.de, "Preise inkl. MwSt.", 21.11.2026 09:20
CARD_DE_EUR_MAX = 6022.69           # same page, highest of 10 offers
card_import = CARD_DE_EUR_MIN / (1 + VAT_DE) * EUR_CHF * (1 + VAT_CH)   # German price -> CH VAT (computed)
CARD = {"low": card_import, "central": CARD_CH_LOW, "high": CARD_CH_HIGH}
# Platform (2U 1P chassis, EPYC CPU, RAM, SSD, redundant PSU), per box. ASSUMPTION anchored on the Supermicro EU
# store page for AS-2115HE-FTNR (2U 1P, up to 4 GPUs): EUR 2,642.07 to 6,924.49 shown, contents and VAT unclear.
PLATFORM = {"low": 5000.0, "central": 8000.0, "high": 12000.0}
# Heat capture at the box: closed enclosure + air-to-water coil + fans + controls, per box. ASSUMPTION (no price).
HEAT_CAPTURE = {"low": 1000.0, "central": 2500.0, "high": 4000.0}
# House integration (hydraulic connection to the tank, pump, valves, pipes, insulation, labour, electrician,
# commissioning), per HOUSE. Proxy: BFE/EnergieSchweiz 2015 study of installed air/water heat pumps (9 kW):
# system price min 26,000 / median 36,000 / max 49,000 CHF excl. VAT; shares labour 17 %, further material 7-8 %,
# electrical 7-8 %, pipe insulation and commissioning 2-4 % each. We take 17 + 7.5 + 7.5 + 3 + 3 = 38 % (computed).
BFE_SYSTEM = {"low": 26000.0, "central": 36000.0, "high": 49000.0}
INTEGRATION_SHARE = 0.17 + 0.075 + 0.075 + 0.03 + 0.03
HOUSE_INTEGRATION = {k: v * INTEGRATION_SHARE * (1 + VAT_CH) for k, v in BFE_SYSTEM.items()}
# Possible house-connection upgrade for 6-8 kW of extra continuous load, per house. ASSUMPTION.
GRID_UPGRADE = {"low": 0.0, "central": 0.0, "high": 5000.0}
# Yearly fixed costs per house (only in the variant line): internet line, ASSUMPTION 100 CHF/month;
# maintenance 2 % of box hardware per year, ASSUMPTION.
NET_CHF_YR = 1200.0
MAINT_SHARE_YR = 0.02

# r3 'share needed' line (docs/overnight.md, research/r3-machine-and-income.md), for comparison
R3_LIST = {"low": 4.298, "central": 9.359, "high": 30.704}   # CHF per server-h, laptop J1 + B200-slice J2
R3_FULL_SHARE = (0.20, 0.30)  # laptop-class hardware, 5 y, N=6: at 100 % / 67 % sold (central)


def work_per_server_hour(power_case, audio_s=AUDIO_S_PER_SAMPLE, samples_s=WHISPER_SAMPLES_S):
    p = wall_kw(power_case)
    audio_h_per_box_h = samples_s * audio_s            # audio-seconds per second = audio-hours per hour
    tok_per_box_h = LLAMA_TOK_S * 3600.0
    return audio_h_per_box_h / p, tok_per_box_h / p     # per kWh = per case server-hour


def list_value(power_case, price_case, audio_s=AUDIO_S_PER_SAMPLE, j1_usd=None):
    a, t = work_per_server_hour(power_case, audio_s)
    j1 = a * (j1_usd if j1_usd is not None else J1_USD_PER_AUDIO_H[price_case]) * USD_CHF
    j2 = t / 1e6 * J2_USD_PER_M_OUT[price_case] * USD_CHF
    return j1, j2, MIX_J1 * j1 + (1 - MIX_J1) * j2


def box_cost(cost_case):
    return N_GPU * CARD[cost_case] + PLATFORM[cost_case] + HEAT_CAPTURE[cost_case]


def installed_per_house(n_servers, power_case, cost_case):
    boxes = n_servers / wall_kw(power_case)             # 1 server = 1 kW = 1/P boxes
    return (boxes * box_cost(cost_case) + HOUSE_INTEGRATION[cost_case] + GRID_UPGRADE[cost_case]), boxes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=float, nargs="+", default=[5.0, 8.0])
    ap.add_argument("--sold", type=float, default=0.67, help="sold share s (case convention: unsold hours still run)")
    ap.add_argument("--operator-share", type=float, default=0.20, help="w, share of list price reaching the operator")
    args = ap.parse_args()
    rows = load()
    print("r4_machine.py. Currency CHF; 1 USD = %.4f CHF, 1 EUR = %.4f CHF (ECB 20 Nov 2026); Swiss VAT %.1f%%."
          % (USD_CHF, EUR_CHF, VAT_CH * 100))
    print("LIST VALUE = what end customers pay a provider at public batch prices, NOT the operator's income.\n")

    print("== 1. Reference machine: 2U 1P server, 4 x RTX PRO 4500 Blackwell Server Edition ==")
    for c in ("low", "central", "high"):
        g, cpu, rest, eff = POWER_CASES[c]
        print(f"  wall power {c:<8} {wall_kw(c)*1000:6.0f} W  = (4 x 165 W x {g:.2f} + CPU {cpu:.0f} W + rest {rest:.0f} W)"
              f" / PSU {eff:.2f}   [ASSUMPTION on SOURCED 165 W and 320 W maxima]")
    print(f"  box throughput: whisper-large-v3 {WHISPER_SAMPLES_S} samples/s x {AUDIO_S_PER_SAMPLE} s = "
          f"{WHISPER_SAMPLES_S*AUDIO_S_PER_SAMPLE:,.0f} audio-h per box-hour ({WHISPER_SAMPLES_S*AUDIO_S_PER_SAMPLE_MAX:,.0f} "
          f"if every sample were 30 s); HPE DL345 cross-check {WHISPER_SAMPLES_S_HPE*AUDIO_S_PER_SAMPLE:,.0f}")
    print(f"                  llama3.1-8b fp4 {LLAMA_TOK_S:,.2f} output tok/s = {LLAMA_TOK_S*3600/1e6:.2f} M per box-hour"
          "   [SOURCED, MLPerf v6.1 6.1-0017 / 6.1-0056]")
    print("  work per case server-hour (= per kWh at the wall):")
    print(f"  {'power':<9}{'audio-h/kWh':>12}{'Wh/audio-h':>11}{'M tok/kWh':>10}")
    for c in ("low", "central", "high"):
        a, t = work_per_server_hour(c)
        print(f"  {c:<9}{a:>12,.0f}{1000/a:>11.3f}{t/1e6:>10.2f}")
    print("  compare: laptop rule (i) 667-755 audio-h/kWh (1.3-1.5 Wh); 8 x B200 slice 1,988 audio-h/kWh (0.50 Wh) and"
          " 56.07 M tok/kWh   [r3, COMPUTED]")

    print("\n== 2. Installed cost (CHF incl. 8.1% VAT) ==")
    print(f"  GPU card: low {CARD['low']:,.0f} (cheapest German offer EUR {CARD_DE_EUR_MIN:,.2f} incl. 19% VAT -> ex VAT"
          f" -> CHF + 8.1%), central {CARD['central']:,.0f} (post.ch), high {CARD['high']:,.0f} (ldlc.ch)")
    for c in ("low", "central", "high"):
        print(f"  {c:<8} box: 4 cards {N_GPU*CARD[c]:>7,.0f} + platform {PLATFORM[c]:>6,.0f} + heat capture"
              f" {HEAT_CAPTURE[c]:>5,.0f} = {box_cost(c):>7,.0f} per box = {box_cost(c)/wall_kw('central'):>7,.0f} per kW"
              f" (central power) | house integration {HOUSE_INTEGRATION[c]:>6,.0f} + grid {GRID_UPGRADE[c]:>5,.0f} per house")
    print(f"  house integration = {INTEGRATION_SHARE*100:.0f}% of the BFE 2015 heat-pump system price "
          f"(26,000 / 36,000 / 49,000 excl. VAT) + 8.1% VAT   [COMPUTED from SOURCED shares; 2015 prices]")

    for n in (6, 8):
        r = simulate(rows, n)
        run_h = r["run_h"]
        op_cost_h = (r["elec"] - r["heat_val"]) / run_h
        print(f"\n== 3. N = {n}: {run_h:,.0f} server-h/yr, coverage {r['coverage']*100:.1f}%, dumped {r['dumped']:.0f} kWh,"
              f" electricity - heat = {op_cost_h:.4f} CHF per server-h   [COMPUTED, baseline_sweep.simulate] ==")
        a, t = work_per_server_hour("central")
        print(f"  work per year if every permit hour is filled (UNLIMITED DEMAND ASSUMED), central power, 50/50:")
        print(f"    J1 {a*run_h*MIX_J1/1e6:.1f} M audio-h/yr ({a*run_h*MIX_J1/365:,.0f} per day);"
              f" J2 {t*run_h*(1-MIX_J1)/1e9:,.0f} bn output tokens/yr")
        print(f"    audio volume at 32 kbit/s (ASSUMPTION): {a*run_h*MIX_J1/365*3600*32e3/8/1e12:.2f} TB per day"
              f" = {a*run_h*MIX_J1/365*3600*32e3/86400/1e6:.0f} Mbit/s sustained into the house")
        inst_c, boxes_c = installed_per_house(n, "central", "central")
        print(f"  installed cost per house (central): {inst_c:,.0f} CHF for {boxes_c:.2f} boxes"
              f" ({inst_c/n:,.0f} per 1 kW server)")
        print("  CHF needed per sold server-h (100%% sold, no interest): operation %.4f; + install 5 y %.3f; 8 y %.3f"
              % (op_cost_h, op_cost_h + inst_c / (5 * run_h), op_cost_h + inst_c / (8 * run_h)))
        print(f"  list value per server-h (central power):         J1     J2   mix 50/50")
        for pc in ("low", "central", "high"):
            j1, j2, mix = list_value("central", pc)
            print(f"    price {pc:<8}                              {j1:6.2f} {j2:6.2f} {mix:6.2f}   (r3 mix: {R3_LIST[pc]:.2f})")
        print("  SHARE OF LIST PRICE the operator must capture (mix 50/50, central power, 100% of run hours sold;"
              f" in brackets: {args.sold:.0%} sold, unsold hours still run):")
        hdr = f"    {'cost case':<9}{'price':<9}{'operation':>14}"
        for y in args.years:
            hdr += f"{'+install ' + format(y, 'g') + ' y':>18}"
        hdr += f"{'+fixed/yr ' + format(args.years[0], 'g') + ' y':>20}"
        print(hdr)
        for cc in ("low", "central", "high"):
            inst, boxes = installed_per_house(n, "central", cc)
            fixed_yr = NET_CHF_YR + MAINT_SHARE_YR * boxes * box_cost(cc)
            for pc in ("low", "central", "high"):
                mix = list_value("central", pc)[2]
                line = f"    {cc:<9}{pc:<9}"
                sh = op_cost_h / mix
                line += f"{sh*100:>7.1f}% ({sh/args.sold*100:4.1f}%)"
                for y in args.years:
                    sh = (op_cost_h + inst / (y * run_h)) / mix
                    line += f"{sh*100:>10.1f}% ({sh/args.sold*100:4.1f}%)"
                y0 = args.years[0]
                sh = (op_cost_h + inst / (y0 * run_h) + fixed_yr / run_h) / mix
                line += f"{sh*100:>12.1f}% ({sh/args.sold*100:4.1f}%)"
                print(line)
        print(f"  payback at operator share w = {args.operator_share:.0%}, sold s = {args.sold:.0%} (case convention:"
              " unsold permit hours still run as heaters), central costs, no interest:")
        for pc in ("low", "central", "high"):
            mix = list_value("central", pc)[2]
            income = args.operator_share * args.sold * run_h * mix
            margin = income - (r["elec"] - r["heat_val"])
            pb = inst_c / margin if margin > 0 else float("inf")
            print(f"    price {pc:<8} income {income:>9,.0f} CHF/yr, minus electricity-heat {r['elec']-r['heat_val']:>6,.0f}"
                  f" = {margin:>9,.0f} CHF/yr -> payback {pb:5.1f} y on {inst_c:,.0f} CHF"
                  + ("  (does NOT pay back in 8 y)" if pb > 8 else ""))

    print("\n== 4. Sensitivity, N = 6, central price, share needed for 5-y payback (100% sold) ==")
    r = simulate(rows, 6)
    run_h = r["run_h"]
    op_cost_h = (r["elec"] - r["heat_val"]) / run_h

    def share(power_case="central", cost_case="central", audio_s=AUDIO_S_PER_SAMPLE, j1_usd=None, years=5.0):
        mix = list_value(power_case, "central", audio_s, j1_usd)[2]
        inst, _ = installed_per_house(6, power_case, cost_case)
        return op_cost_h / mix, (op_cost_h + inst / (years * run_h)) / mix
    base = share()
    print(f"  base (central power, cost, price)                      operation {base[0]*100:5.1f}%  5-y {base[1]*100:5.1f}%")
    for label, kw in (("wall power low (0.75 kW per box)", dict(power_case="low")),
                      ("wall power high (1.22 kW per box)", dict(power_case="high")),
                      ("cost low", dict(cost_case="low")), ("cost high", dict(cost_case="high")),
                      ("30 s of audio per MLPerf sample", dict(audio_s=AUDIO_S_PER_SAMPLE_MAX)),
                      ("J1 priced as large-v3 batch (0.0555 USD/audio-h)", dict(j1_usd=J1_USD_LARGE_V3_BATCH))):
        s = share(**kw)
        print(f"  {label:<55}operation {s[0]*100:5.1f}%  5-y {s[1]*100:5.1f}%")
    for label, frac in (("J1 only (mix 100/0)", 1.0), ("J2 only (mix 0/100)", 0.0)):
        j1, j2, _ = list_value("central", "central")
        mix = frac * j1 + (1 - frac) * j2
        inst, _ = installed_per_house(6, "central", "central")
        print(f"  {label:<55}operation {op_cost_h/mix*100:5.1f}%  5-y {(op_cost_h + inst/(5*run_h))/mix*100:5.1f}%")
    print("\n== 5. Cross-check: renting the box by the hour instead of selling work (N = 6, central power and cost) ==")
    print("  renter prices per GPU-hour, read 21 Nov 2026 [SOURCED]: GPU.ai 0.41 (cheapest, getdeploying.com),"
          " RunPod Secure Cloud 0.72 (runpod.io), median of 7 providers 0.92 (getdeploying.com)")
    print("  These are prices for data-centre-hosted, always-available GPUs. A heat-following basement host is not"
          " shown to get them (r2: hosts must stay available).")
    inst6, _ = installed_per_house(6, "central", "central")
    per_server = inst6 / 6
    h_per_server = run_h / 6
    mix_c = list_value("central", "central")[2]
    for label, usd in (("cheapest 0.41", 0.41), ("RunPod 0.72", 0.72), ("median 0.92", 0.92)):
        renter = N_GPU * usd * USD_CHF / wall_kw("central")       # CHF per kWh-server-hour
        host = 0.8 * renter                                        # ~80 % host share (r2, sourced)
        net = host - op_cost_h
        pb = per_server / (net * h_per_server) if net > 0 else float("inf")
        print(f"    {label:<14} renter {renter:5.2f} CHF per server-h = {renter/mix_c*100:4.1f}% of central list value;"
              f" host (x0.8) {host:4.2f}; net {net:4.2f}; payback {pb:4.1f} y on {per_server:,.0f} CHF per server"
              f" (all {h_per_server:,.0f} permit h/yr rented)")
    print(f"\n  r3 line for comparison (laptop J1 + B200-slice J2, laptop-class hardware 52,329 CHF/kW, N=6, 5 y, central):"
          f" operation {0.2261/R3_LIST['central']*100:.1f}%, full {R3_FULL_SHARE[0]*100:.0f}% ({R3_FULL_SHARE[1]*100:.0f}% at 67% sold)")
    print("  NOTE: hardware's share of list value does not depend on wall power (cost per kW and work per kWh both"
          " scale with 1/P); only the electricity term and the per-house items do.")


if __name__ == "__main__":
    main()

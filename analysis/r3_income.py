"""Round 3, weak point "machine and income": computing income from a PRICE PER JOB.

Exploratory. Not the team's scheduler or dashboard. Standard library only.

    python3 analysis/r3_income.py                              # laptop E from the round-3 probe
    python3 analysis/r3_income.py --wh-per-audio-hour 0.9      # Saturday's own measured value
    python3 analysis/r3_income.py --wholesale 0.3 --sold 0.8

Idea: GPU marketplaces rent HOURS of machines that stay available (round 2). A
heat-following server cannot promise hours, but it can deliver finished WORK before
a deadline. Batch tiers sell exactly that (a result inside 24 h to 7 days). So the
income line is: work done x market price of that work.

The market price is a public LIST price per audio-hour / per million tokens: what
the END CUSTOMER pays a provider. It is NOT what DigitalHeat would earn. The script
prints the gross list value first, then applies two labelled haircuts:
  wholesale share w = share of the list price that reaches the machine operator
  sold share s      = share of heat-permit server-hours that carry paid work

Server-hours, electricity cost and heat value come unchanged from
analysis/baseline_sweep.py (simulate, policy 'follow', case assumptions).

Status labels:  SOURCED    = read on the page named, 2026-11-21
                COMPUTED   = arithmetic on sourced numbers, or script output
                ASSUMPTION = our choice
"""
import argparse
import sys

sys.dont_write_bytecode = True  # do not touch analysis/__pycache__
import baseline_sweep as bs  # noqa: E402

FX = 0.8392  # CHF per USD. SOURCED in round 1: ECB reference rates of 20 Nov 2026 (EUR/USD 1.0990, EUR/CHF 0.9223).
BREAK_EVEN = 0.2261  # CHF per server-hour, case formula. COMPUTED by baseline_sweep.py (identical for any N, follow).

# ---------------------------------------------------------------- J1 work per server-hour
# Scaling rule (i), equal energy per unit of work, GROSS laptop energy:
#   audio-hours per 1 kW server-hour = 1000 Wh / E,   E = laptop Wh per audio-hour
E_PROBE = 1.50  # Wh per audio-hour (1.500 printed). COMPUTED: python3 analysis/r3_whisper_energy_probe.py, 2026-11-21,
#   M3 Pro, whisper-large-v3-turbo, synthetic TTS audio, battery-controller telemetry (see research file).
E_BRACKET = [  # Wh per audio-hour of other machines, for the error range of rule (i)
    (0.35, "Apple M4 Max, turbo, MLX, 25 W as posted by one user (chip power?)", "COMPUTED from SOURCED"),
    (0.503, "8 x B200 server, large-v3, MLPerf v5.1 ID 5.1-0061, 7,636 W official power result", "COMPUTED from SOURCED; audio per sample approximate"),
    (2.22, "2 x Xeon 6787P, no GPU, large-v3, MLPerf v6.1 ID 6.1-0032, 20.39 samples/s", "power NOT measured: 1 kW ASSUMPTION"),
    (6.7, "2 x RTX 4090 in a 1 kW rig, large-v3, one 2023 blog post", "UNVERIFIED; 1 kW ASSUMPTION"),
]
J1_AUDIO_H_PER_KWH_B200 = 1988.0  # COMPUTED (r3_mlperf_power.py): 688.623 samples/s, 22.05 s per sample, 7,636.5 W
J1_AUDIO_H_PER_KWH_CPU = 20.3947 * 22.05  # 450 audio-h per hour; per kWh only if 1 kW: ASSUMPTION

# ---------------------------------------------------------------- J2 work per server-hour
J2_TOK_PER_KWH_B200 = 56.07e6  # output tokens per kWh. COMPUTED from MLPerf v5.1 ID 5.1-0062:
#   146,960 tokens/s (SOURCED) at 9,436.05 W (SOURCED: official Power_Result in summary_results.json). fp4 weights.
J2_TOK_PER_KWH_CPU = 1227.99 * 3600  # 4.42 million per hour, MLPerf v6.1 ID 6.1-0032. Per kWh only if 1 kW: ASSUMPTION.

# ---------------------------------------------------------------- job sizes and mix (plan)
J1_SERVER_H = 0.5    # ASSUMPTION (plan; analysis/r2_deadline_sim.py)
J2_SERVER_H = 4.0    # ASSUMPTION (plan)
J1_SHARE = 0.5       # ASSUMPTION: half of the server-hours go to each job type

# ---------------------------------------------------------------- prices of the WORK, USD, read 2026-11-21
P1 = {  # USD per audio-hour
    "low": (0.012, "DeepInfra openai/whisper-large-v3-turbo list '$0.00020 / minute' x60. SOURCED https://deepinfra.com/openai/whisper-large-v3-turbo"),
    "central": (0.020, "Groq whisper-large-v3-turbo '$0.04' per hour, Batch API '50% cost discount'. SOURCED https://console.groq.com/docs/speech-to-text + /docs/batch"),
    "high": (0.045, "Together AI Whisper Large v3 '$0.0015' per audio minute x60, batch '50% off' for openai/whisper-large-v3. SOURCED https://www.together.ai/pricing + docs.together.ai/docs/inference/batch/overview "
                    "(if $0.0015 is already the batch figure the price is 0.090: UNVERIFIED which)"),
}
IN_PER_OUT = 6.0  # ASSUMPTION: input tokens billed per output token (MLPerf task = news summarisation, 128 output tokens). Not sourced.
P2 = {  # USD per million OUTPUT tokens, input tokens added at IN_PER_OUT where stated
    "low": (0.04, "DeepInfra Meta-Llama-3.1-8B-Instruct-Turbo output $0.04 per 1M, input ignored. SOURCED https://deepinfra.com/pricing"),
    "central": (0.04 + IN_PER_OUT * 0.02, "same, output $0.04 + 6 x input $0.02. Prices SOURCED, ratio 6 ASSUMPTION"),
    "high": (0.11 + IN_PER_OUT * 0.11, "Amazon Bedrock Llama 3.1 Instruct (8B) batch $0.11 in / $0.11 out per 1M (on-demand $0.22/$0.22). "
                                       "SOURCED https://aws.amazon.com/bedrock/pricing/ (rendered page, default region); ratio 6 ASSUMPTION"),
}

WHOLESALE = 0.20  # ASSUMPTION: share of the list price reaching the machine operator. No source; cross-check in section 6.
SOLD = 0.67       # ASSUMPTION: share of heat-permit hours with paid work.


def chf(usd):
    return usd * FX


def work_values(j1_ah_per_sh, j2_tok_per_sh):
    """Gross list value in CHF of one server-hour, per type and for the mix."""
    v1 = {k: chf(P1[k][0]) * j1_ah_per_sh for k in P1}
    v2 = {k: chf(P2[k][0]) * j2_tok_per_sh / 1e6 for k in P2}
    mix = {k: J1_SHARE * v1[k] + (1 - J1_SHARE) * v2[k] for k in P1}
    return v1, v2, mix


def row(label, d, fmt="{:>10.3f}"):
    return f"{label:<44}" + "".join(fmt.format(d[k]) for k in ("low", "central", "high"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--wh-per-audio-hour", type=float, default=E_PROBE, help="laptop gross Wh per audio-hour")
    ap.add_argument("--wholesale", type=float, default=WHOLESALE)
    ap.add_argument("--sold", type=float, default=SOLD)
    a = ap.parse_args()
    e, w, s = a.wh_per_audio_hour, a.wholesale, a.sold
    j1 = 1000.0 / e
    j2 = J2_TOK_PER_KWH_B200
    rows = bs.load()

    print(f"r3_income.py. Currency CHF; 1 USD = {FX} CHF (ECB, 20 Nov 2026). LIST PRICES ARE WHAT END CUSTOMERS PAY A PROVIDER,")
    print("not DigitalHeat's income. Break-even = case formula, heat credited at electricity price / 2.5.\n")

    print("== 1. Inputs ==")
    print(f"J1 scaling rule (i): audio-h per server-h = 1000 / E = {j1:,.0f}, E = {e:g} Wh per audio-hour "
          f"[{'r3_whisper_energy_probe.py, COMPUTED' if e == E_PROBE else '--wh-per-audio-hour'}]")
    print(f"J2: {j2/1e6:.2f} million output tokens per server-h [COMPUTED, MLPerf 5.1-0062, 1 kW slice of a 9.4 kW machine]")
    print(f"Job sizes [ASSUMPTION]: J1 = {J1_SERVER_H} server-h = {J1_SERVER_H*j1:,.0f} audio-h; J2 = {J2_SERVER_H:g} server-h = {J2_SERVER_H*j2/1e6:,.0f} million output tokens")
    print(f"Mix [ASSUMPTION]: {J1_SHARE:.0%} of server-hours to J1, {1-J1_SHARE:.0%} to J2")
    for k in P1:
        print(f"J1 {k:<8} {P1[k][0]:.3f} USD/audio-h = {chf(P1[k][0])*J1_SERVER_H*j1:6.2f} CHF per J1 job  [{P1[k][1]}]")
    for k in P2:
        print(f"J2 {k:<8} {P2[k][0]:.3f} USD/M out-tok = {chf(P2[k][0])*J2_SERVER_H*j2/1e6:6.2f} CHF per J2 job  [{P2[k][1]}]")
    print(f"Wholesale share w = {w:.0%} [ASSUMPTION]; sold share s = {s:.0%} [ASSUMPTION]")

    print("\n== 2. Gross list value of the work in one 1 kW server-hour (CHF) ==")
    print(f"{'':<44}{'low':>10}{'central':>10}{'high':>10}")
    v1, v2, mix = work_values(j1, j2)
    print(row(f"J1, rule (i), E = {e:g}", v1))
    print(row("J2, B200 slice", v2))
    print(row("mix 50/50 (the main case)", mix))
    print(f"{'break-even (electricity - heat value)':<44}{BREAK_EVEN:>10.4f}   (0.3325 without the heat credit)")
    print("share of list value needed to cover electricity minus heat value (= break-even / gross value):")
    for lab, v in (("J1", v1), ("J2, B200 slice", v2), ("mix 50/50", mix)):
        print(row("  " + lab, {k: BREAK_EVEN / v[k] for k in v}, "{:>10.1%}"))

    print("\n== 3. Same, for three coherent machines (one efficiency for both job types) ==")
    for lab, a1, a2, note in (
            ("laptop-class (rule i) J1 + B200 J2", j1, j2, "the main case"),
            ("8 x B200, 1 kW slice", J1_AUDIO_H_PER_KWH_B200, J2_TOK_PER_KWH_B200, "power SOURCED (MLPerf official)"),
            ("2 x Xeon 6787P, no GPU", J1_AUDIO_H_PER_KWH_CPU, J2_TOK_PER_KWH_CPU, "1 kW ASSUMPTION")):
        _, _, m = work_values(a1, a2)
        print(row(f"  {lab}", m) + f"   needs {BREAK_EVEN/m['central']:.1%} of list (central)  [{note}]")

    print("\n== 4. J1 over the scaling bracket, central price ==")
    for ee, lab, st in [(e, "laptop, this run", "COMPUTED")] + E_BRACKET:
        g = chf(P1["central"][0]) * 1000 / ee
        print(f"  E = {ee:>5.3g} -> {1000/ee:>6,.0f} audio-h per server-h -> {g:6.2f} CHF -> needs {BREAK_EVEN/g:5.1%}   [{lab}; {st}]")

    print("\n== 5. Year on the reference house, follow policy, every permit hour filled with work ==")
    for n in (6, 8):
        r = bs.simulate(rows, n)
        H = r["run_h"]
        h1, h2 = H * J1_SHARE, H * (1 - J1_SHARE)
        net = r["elec"] - r["heat_val"]
        gross = {k: h1 * v1[k] + h2 * v2[k] for k in P1}
        print(f"\nN = {n}: server-hours run {H:,.0f}; coverage {r['coverage']:.1%}; dumped {r['dumped']:.0f} kWh  [COMPUTED, baseline_sweep.simulate]")
        print(f"  J1: {h1:,.0f} server-h = {h1/J1_SERVER_H:,.0f} jobs = {h1*j1/1e6:.2f} million audio-h ({h1*j1/365:,.0f} per day)")
        print(f"  J2: {h2:,.0f} server-h = {h2/J2_SERVER_H:,.0f} jobs = {h2*j2/1e9:,.0f} billion output tokens")
        print(f"  electricity {r['elec']:,.0f} CHF; heat value {r['heat_val']:,.0f} CHF; electricity - heat {net:,.0f} CHF = {net/H:.4f} per server-h")
        print(f"  {'':<42}{'low':>12}{'central':>12}{'high':>12}")
        print(f"  {'A. gross LIST value of the work, CHF/yr':<42}" + "".join(f"{gross[k]:>12,.0f}" for k in gross))
        print(f"  {'   per server-hour':<42}" + "".join(f"{gross[k]/H:>12.3f}" for k in gross))
        print(f"  {'   margin over 0.2261 per server-hour':<42}" + "".join(f"{gross[k]/H-BREAK_EVEN:>12.3f}" for k in gross))
        inc = {k: gross[k] * w * s for k in gross}
        print(f"  B. scenario w = {w:.0%}, s = {s:.0%}; all permit hours run (heat kept), unsold hours unpaid  [case convention]")
        print(f"  {'   server-hours sold':<42}{H*s:>12,.0f}")
        print(f"  {'   computing income, CHF/yr':<42}" + "".join(f"{inc[k]:>12,.0f}" for k in inc))
        print(f"  {'   electricity / heat value, CHF/yr':<42}{r['elec']:>12,.0f}{r['heat_val']:>12,.0f}")
        print(f"  {'   income per sold server-hour':<42}" + "".join(f"{inc[k]/(H*s):>12.3f}" for k in inc))
        print(f"  {'   case break-even per sold hour':<42}{net/(H*s):>12.4f}")
        print(f"  {'   margin per sold server-hour':<42}" + "".join(f"{(inc[k]-net)/(H*s):>12.3f}" for k in inc))
        print(f"  {'   yearly margin before hardware, CHF':<42}" + "".join(f"{inc[k]-net:>12,.0f}" for k in inc))
        print(f"  C. sold share at which income = electricity - heat value, s* = (elec - heat) / (gross x w):")
        for ww in (0.05, 0.10, w, 0.50, 1.00):
            print(f"  {'   w = ' + format(ww, '.0%'):<42}" + "".join(f"{min(9.99, net/(gross[k]*ww)):>12.1%}" for k in gross)
                  + ("   (>100% = cannot break even)" if any(net / (gross[k] * ww) > 1 for k in gross) else ""))
        print(f"  D. plan default (server OFF when unsold): margin = s x run-h x (w x gross/h - 0.2261); sign set by w alone:")
        print(f"  {'   w needed':<42}" + "".join(f"{net/gross[k]:>12.1%}" for k in gross) + "   (coverage then falls with s)")

    print("\n== 6. Cross-check of the wholesale share (not a source for it) ==")
    rt = 600 / 8  # RTX 4090, 10 min of audio in 8 s (one blog post, UNVERIFIED) = 75 audio-h per GPU-hour
    for k in P1:
        val = rt * P1[k][0]
        print(f"  RTX 4090 at {rt:.0f} x real time: list value {val:.2f} USD per GPU-hour ({k}); Salad renter price 0.160-0.440 USD/h "
              f"= {0.160/val:.0%}-{0.440/val:.0%} of it")
    print("  A provider renting that GPU and keeping it busy would hand the machine owner about this share (after the ~20% marketplace fee: x0.8).")

    print("\n== 7. Efficiency is bought with hardware: J1 list value vs hardware cost per run hour (N = 6, central price) ==")
    r6 = bs.simulate(rows, 6)
    h_per_srv = r6["run_h"] / 6  # mean run hours per server per year
    life = 5.0  # years, ASSUMPTION (plan)
    for lab, ee, chf_per_kw, st in (
            ("laptop-class (M3 Pro), this run", e, 2000.0 * 1000.0 / 38.22,
             "2,000 CHF per laptop ASSUMPTION (price not read), 38.22 W per laptop COMPUTED by the probe"),
            ("2 x RTX 4090 rig", 6.7, 6000.0, "6,000 CHF per kW = round-2 ASSUMPTION on a SOURCED card floor price; E UNVERIFIED")):
        hw = chf_per_kw / (life * h_per_srv)
        g = chf(P1["central"][0]) * 1000 / ee
        print(f"  {lab}: hardware {chf_per_kw:,.0f} CHF/kW / ({life:g} yr x {h_per_srv:,.0f} h) = {hw:.3f} CHF per run hour; "
              f"J1 list value {g:.2f}; electricity - heat + hardware = {BREAK_EVEN+hw:.3f} = {(BREAK_EVEN+hw)/g:.0%} of list value "
              f"(at s = {s:.0%}: w needed {(BREAK_EVEN+hw)/(g*s):.0%})  [{st}]")
    print("  No hardware price was read for the 8 x B200 server; its row is left out on purpose.")


if __name__ == "__main__":
    main()

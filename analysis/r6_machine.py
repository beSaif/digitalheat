"""Round 6: machine identity behind the realism column (exploratory, 2026-11-21).

NOT the team's scheduler. Standard library only. Imports (never edits) analysis/baseline_sweep.py,
analysis/r4_machine.py and analysis/r5_chain.py. Sources and status of every input:
docs/research/r6-machine-identity.md.

    python3 analysis/r6_machine.py

Question: can price, wall power and throughput (J1 whisper, J2 llama3.1-8b) come from ONE liquid-cooled
configuration? Candidate machines compared on the same cost and price rules as r4/r5:

  R5     plan as of round 5: 4 x RTX PRO 4500 Server Edition (MLPerf throughput, 165 W cards, air-cooled as
         measured) costed with Alphacool blocks that fit the WORKSTATION card. Inconsistent (open risk 5).
  R5WS   the box the costed blocks actually fit: 4 x RTX PRO 4500 workstation (200 W, sourced by the r5
         critic). Wall power on r4's model; throughput NOT measured -> assumed equal to the server card.
  PRO6K4 4 x RTX PRO 6000 Blackwell Server Edition (600 W TGP) + cold plates made for that exact edition
         (Alphacool ES / EK-Pro / JetCool SmartPlate). J2 measured on a vendor DLC box with these four cards
         (MLPerf v6.1 6.1-0102, ManyCoreSoft DeepGadget dg5W, "Direct Liquid Cooling"); J1 measured on the
         air-cooled Cisco X215c with the same four cards at the same 600 W TGP (6.1-0019), whose J2 is within
         1.6 % of the DLC box. Card price sourced (German shops, 21 Nov 2026). Wall power ESTIMATED.
  PRO6K1 1 x RTX PRO 6000 SE box near 1 kW: throughput = 4-GPU result / 4 (ASSUMPTION), wall power estimated.
  B200LC Lenovo ThinkSystem SR780a V3, 8 x B200, "Water-cooled" (Neptune, W45 inlet): J1 and J2 on the SAME
         system in MLPerf v5.1 (5.1-0062), J2 with MEASURED wall power (9,436 W). No price found -> the script
         prints the box price at which it would need the same share as PRO6K4 instead of a share.

Everything is normalised to the case's server: 1 server = 1 kW = 1/P boxes. Operation cost per server-hour
and the temperature chain come from r5_chain.sim (follow rule, never dumps, tank loss 2.80 kWh/day).
Maintenance, retrofit warranty self-insurance and leak reserve are ASSUMPTIONS, added as yearly costs.
"""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline_sweep as bs          # noqa: E402
import r4_machine as mc              # noqa: E402
import r5_chain as rc                # noqa: E402

USD_CHF, EUR_CHF, VAT_CH, VAT_DE = mc.USD_CHF, mc.EUR_CHF, mc.VAT_CH, mc.VAT_DE
VAT_AT = 0.20                        # Austrian standard VAT (ASSUMPTION: standard rate on the AT shop prices)
AUDIO_S = mc.AUDIO_S_PER_SAMPLE      # 22.05 s of audio per MLPerf whisper sample (r3/r4)


def de_to_ch(eur, vat=VAT_DE):
    """EUR shop price incl. foreign VAT -> CHF incl. Swiss VAT (same rule as r4)."""
    return eur / (1 + vat) * EUR_CHF * (1 + VAT_CH)


# ------------------------------------------------------------------ machines
# throughput per box: (whisper samples/s, llama3.1-8b output tok/s); all SOURCED (MLPerf loadgen summaries)
# power model (n_gpu, gpu_w): wall = (n * gpu_w * g + cpu + rest) / eff with r4's POWER_CASES (ASSUMPTION)
CARD_6K_DE = [20322.99, 20323.00, 21740.79, 21740.84]   # hardwaredealz offers, DE shops, incl. VAT, 21.11.2026 10:20
CARD_6K_AT = [21999.00, 29169.00]                        # hardwaredealz offers, AT shops, incl. VAT, 21.11.2026 10:20
CARD_6K = {"low": de_to_ch(min(CARD_6K_DE)),
           "central": de_to_ch(sorted(CARD_6K_DE)[1] / 2 + sorted(CARD_6K_DE)[2] / 2),
           "high": de_to_ch(max(CARD_6K_AT), VAT_AT)}
BLOCK_CHF = rc.BLOCK_CHF             # Alphacool ES 399.98 EUR incl. DE VAT (same price for the 4500 WS and 6000 SE block)

MACHINES = {
    #          n_gpu gpu_w  whisper_sps          llama_tok_s   card CHF dict      status note
    "R5":     (4, 165.0, mc.WHISPER_SAMPLES_S, mc.LLAMA_TOK_S, mc.CARD,
               "4x RTX PRO 4500 SE (MLPerf 6.1-0017, air) + blocks for another edition"),
    "R5WS":   (4, 200.0, mc.WHISPER_SAMPLES_S, mc.LLAMA_TOK_S, mc.CARD,
               "4x RTX PRO 4500 workstation 200 W + its blocks; throughput ASSUMED = server card"),
    "PRO6K4": (4, 600.0, 145.557, 24511.8, CARD_6K,
               "4x RTX PRO 6000 SE DLC: J2 DeepGadget dg5W DLC 6.1-0102, J1 Cisco X215c 6.1-0019"),
    "PRO6K1": (1, 600.0, 145.557 / 4, 24511.8 / 4, CARD_6K,
               "1x RTX PRO 6000 SE: 4-GPU results / 4 (ASSUMPTION)"),
}
CISCO_6K_LLAMA = 24913.5             # 6.1-0019, air-cooled, same 4 cards: consistency check for the J1 borrow

# B200 water-cooled reference (MLPerf v5.1 5.1-0062, Lenovo SR780a V3, "Water-cooled"): SOURCED
B200LC = {"whisper_sps": 699.136, "llama_tok_s": 146960.0, "llama_w": 9436.05296875,
          "air_twin_whisper_w": 7636.4895833333}   # 5.1-0061 SR680a V3 (air) whisper Offline power
B200LC_FLOW_LPM = 12.0               # Lenovo: min. 12.0 l/min per chassis at 45 C inlet (B200), W45: SOURCED


def wall_kw(machine, case="central"):
    n, gw = MACHINES[machine][0], MACHINES[machine][1]
    g, cpu, rest, eff = mc.POWER_CASES[case]
    return (n * gw * g + cpu + rest) / eff / 1000.0


def work_per_kwh(machine, case="central"):
    _, _, wsps, ltok, _, _ = MACHINES[machine]
    p = wall_kw(machine, case)
    return wsps * AUDIO_S / p, ltok * 3600.0 / p          # audio-h per kWh, tokens per kWh


def list_value(audio_h, tok, price="central", mix=mc.MIX_J1):
    j1 = audio_h * mc.J1_USD_PER_AUDIO_H[price] * USD_CHF
    j2 = tok / 1e6 * mc.J2_USD_PER_M_OUT[price] * USD_CHF
    return j1, j2, mix * j1 + (1 - mix) * j2


# ------------------------------------------------------------------ cost per box and per house
def capture_per_box(machine, case="central"):
    """Cold plates per box: n blocks + CPU plate + manifold/QDs/leak sensor + assembly (r5 rule, ASSUMPTIONS
    except the block price). Per-box extras scale with the 4-GPU r5 values; a 1-GPU box gets a smaller manifold."""
    n = MACHINES[machine][0]
    i = {"low": 0, "central": 1, "high": 2}[case]
    cpu_plate = (150, 250, 400)[i]
    manifold = (500, 800, 1500)[i] if n >= 4 else (300, 500, 900)[i]
    assembly = (240, 360, 600)[i] if n >= 4 else (120, 200, 400)[i]
    return n * BLOCK_CHF + cpu_plate + manifold + assembly


def box_cost(machine, case="central"):
    n, _, _, _, card, _ = MACHINES[machine]
    return n * card[case] + mc.PLATFORM[case] + capture_per_box(machine, case)


def house_items(case="central"):
    _, items = rc.chain_costs("DLC", case)     # buffer, CDU, fresh-water station, DHW cylinder (r5)
    return items


def installed(machine, n_srv, case="central"):
    boxes = n_srv / wall_kw(machine)
    items = house_items(case)
    total = boxes * box_cost(machine, case) + mc.HOUSE_INTEGRATION[case] + mc.GRID_UPGRADE[case] + sum(items.values())
    liquid = boxes * capture_per_box(machine, case) + items["CDU: plate HX + pump group + controls (assumption)"]
    return total, boxes, liquid


# ------------------------------------------------------------------ yearly costs (ASSUMPTIONS, labelled)
SERVICE_H = 4.0          # h per house-year: quick service 30-60 min per loop (sourced range) x boxes + CDU check
SERVICE_CHF_H = 120.0    # CHF per technician hour, incl. travel share (ASSUMPTION)
COOLANT_CHF = 150.0      # CHF per house-year, inhibited coolant / PG25 top-up or change (ASSUMPTION)
SPARES_SHARE = 0.02      # 2 % of liquid-cooling hardware per year: pumps, QDs, O-rings, sensors (ASSUMPTION)
LEAK_RESERVE_BOX = 50.0  # CHF per box-year: expected leak damage net of sensor shutdown (ASSUMPTION)
MTBF_H = 1864500.0       # SOURCED: NVIDIA RTX PRO 6000 SE brief, MTBF uncontrolled env., 35 C
AFR = 8760.0 / MTBF_H    # computed: ~0.47 % of cards fail per year (applied to both card types: ASSUMPTION)
WARRANTY_Y = 3.0         # SOURCED: PNY EMEA, professional graphic cards 3 years


def yearly_cost(machine, n_srv, retrofit=True, case="central"):
    """Maintenance + spares + leak reserve + (retrofit only) self-insured card failures inside the warranty years,
    spread over the payback years by the caller. Returns (fixed per year, warranty self-insurance total)."""
    _, boxes, liquid = installed(machine, n_srv, case)
    n_gpu, _, _, _, card, _ = MACHINES[machine]
    maint = SERVICE_H * SERVICE_CHF_H + COOLANT_CHF + SPARES_SHARE * liquid + LEAK_RESERVE_BOX * boxes
    warranty = (AFR * boxes * n_gpu * card[case] * WARRANTY_Y) if retrofit else 0.0
    return maint, warranty


# ------------------------------------------------------------------ temperature variants for the realism column
# (t_top house side, return limit, sh mode, dhw mode, cop_sh, cop_dhw, pump kW per running server); CDU 5 K approach,
# server-side rise ~10 K at design flow. Inlet limit -> return limit = inlet - 5 K; top = inlet + 10 - 5.
EXTRA_CHAINS = {
    "DLC40": (45.0, 35.0, "direct", "element", None, None, 0.02),   # inlet <= 40 C (W40 class), outlet ~50 C
    "DLC45": rc.CHAINS["DLC"],                                      # r5 plan: inlet <= 45 C, outlet ~55 C
    "DLC50T": (55.0, 45.0, "direct", "element", None, None, 0.02),  # inlet <= 50 C, outlet ~60 C (block max 60 C);
    # r5's own "DLC50" keeps a 50 C top with a 45 C return limit (conservative); printed for comparison
    "DLC55": (60.0, 50.0, "direct", "element", None, None, 0.02),   # inlet <= 55 C, outlet ~65 C: JetCool-class only
}
for k, v in EXTRA_CHAINS.items():
    assert k not in rc.CHAINS or rc.CHAINS[k] == v, k
    rc.CHAINS[k] = v               # runtime only; r5_chain.py on disk is unchanged


def share(be_op, inst, run_h, years, mix, maint=0.0, warranty=0.0):
    return (be_op + inst / (years * run_h) + maint / run_h + warranty / (years * run_h)) / mix


def main():
    rows = bs.load()
    print("r6_machine.py  (CHF; 1 USD = %.4f CHF, 1 EUR = %.4f CHF, ECB 20 Nov 2026; CH VAT %.1f%%, DE %.0f%%, AT %.0f%%)"
          % (USD_CHF, EUR_CHF, VAT_CH * 100, VAT_DE * 100, VAT_AT * 100))
    print("LIST VALUE = public batch prices for the work, NOT operator income. Shares: every permit hour sold, simple payback.")

    print("\n== 0. Regression: R5 machine on this script's rules vs r5_chain section 4 ==")
    r = rc.sim(rows, 6, "DLC", "underfloor 35/28", tank_loss=rc.LOSS)
    tot_r5, _, _, _ = rc.installed(6, "DLC")
    tot_me, _, _ = installed("R5", 6)
    a, t = work_per_kwh("R5")
    mix = list_value(a, t)[2]
    print(f"  r5_chain installed N=6 {tot_r5:,.0f} CHF | r6 {tot_me:,.0f} CHF -> {'OK' if abs(tot_r5 - tot_me) < 1 else 'MISMATCH'}")
    print(f"  r5 list value {mc.list_value('central', 'central')[2]:.4f} | r6 {mix:.4f}; "
          f"5-y share r6 {share(r['be_chg'], tot_me, r['run_h'], 5, mix)*100:.2f}% (plan: 11.2%)")

    print("\n== 1. Machines: wall power (r4 power model, ASSUMPTION on SOURCED TGP), work per kWh, list value ==")
    print(f"  {'machine':<8}{'P low/cen/high kW':>20}{'audio-h/kWh':>12}{'M tok/kWh':>10}{'list CHF/srv-h':>15}  note")
    for m in MACHINES:
        a, t = work_per_kwh(m)
        print(f"  {m:<8}{wall_kw(m,'low'):>6.2f}/{wall_kw(m):.2f}/{wall_kw(m,'high'):.2f}{a:>14,.0f}{t/1e6:>10.2f}"
              f"{list_value(a, t)[2]:>15.2f}  {MACHINES[m][5]}")
    print(f"  J1 borrow check: DLC dg5W llama {MACHINES['PRO6K4'][3]:,.1f} vs air Cisco X215c {CISCO_6K_LLAMA:,.1f} tok/s "
          f"-> ratio {MACHINES['PRO6K4'][3]/CISCO_6K_LLAMA:.4f}")
    b_a = B200LC["whisper_sps"] * AUDIO_S / (B200LC["air_twin_whisper_w"] / 1000)
    b_t = B200LC["llama_tok_s"] * 3600 / (B200LC["llama_w"] / 1000)
    print(f"  B200LC  measured {B200LC['llama_w']/1000:.2f} kW (J2 run){b_a:>12,.0f}{b_t/1e6:>10.2f}{list_value(b_a, b_t)[2]:>15.2f}"
          "  SR780a V3 water-cooled; J1 power from the air twin SR680a (5.1-0061)")
    cap_kw = 0.85 * B200LC["llama_w"] / 1000      # ASSUMPTION: 85 % of wall power to water (r5 computed 84.5 % for DLC)
    rise = cap_kw / (B200LC_FLOW_LPM / 60.0 * 4.186)
    print(f"  B200LC water rise at 12.0 l/min, 85% capture (ASSUMPTION): {rise:.1f} K -> 45 C in, ~{45+rise:.0f} C out")
    print(f"  card prices CHF incl. CH VAT: RTX PRO 6000 SE low {CARD_6K['low']:,.0f} / central {CARD_6K['central']:,.0f} / "
          f"high {CARD_6K['high']:,.0f} (AT max); RTX PRO 4500 central {mc.CARD['central']:,.0f}")
    print(f"  CHF of card per (audio-h per h): PRO 6000 {CARD_6K['central']/(145.557/4*AUDIO_S):.1f}, "
          f"PRO 4500 {mc.CARD['central']/(mc.WHISPER_SAMPLES_S/4*AUDIO_S):.1f}; per (k tok/s): "
          f"PRO 6000 {CARD_6K['central']/(24511.8/4/1000):,.0f}, PRO 4500 {mc.CARD['central']/(mc.LLAMA_TOK_S/4/1000):,.0f}")

    print("\n== 2. Installed cost and share of list price needed, N = 6 and N = 8 (central costs and prices) ==")
    print("  op = BEchg of the r5 DLC chain (machine-independent per kWh); maint = service + coolant + spares + leak reserve;")
    print("  warranty = self-insured card failures in years 1-3 if the retrofit voids the card warranty (AFR from MTBF)")
    res = {}
    for n in (6, 8):
        r = rc.sim(rows, n, "DLC", "underfloor 35/28", tank_loss=rc.LOSS)
        op, run_h = r["be_chg"], r["run_h"]
        print(f"\n  N={n}: {run_h:,.0f} server-h/yr, BEchg {op:.4f} CHF/server-h")
        print(f"  {'machine':<8}{'boxes':>6}{'box CHF':>10}{'house CHF':>11}{'liquid':>8}{'maint/yr':>9}{'warr.':>7}"
              f"{'op':>6}{'5y':>7}{'5y+m':>7}{'8y':>7}{'8y+m':>7}{'5y+m LLM':>9}")
        for m in MACHINES:
            inst, boxes, liquid = installed(m, n)
            maint, warr = yearly_cost(m, n, retrofit=True)
            a, t = work_per_kwh(m)
            j1, j2, mix = list_value(a, t)
            s = {"op": op / mix, "5": share(op, inst, run_h, 5, mix), "8": share(op, inst, run_h, 8, mix),
                 "5m": share(op, inst, run_h, 5, mix, maint, warr), "8m": share(op, inst, run_h, 8, mix, maint, warr),
                 "5mLLM": share(op, inst, run_h, 5, j2, maint, warr)}
            res[(n, m)] = (inst, s, maint, warr)
            print(f"  {m:<8}{boxes:>6.2f}{box_cost(m):>10,.0f}{inst:>11,.0f}{liquid:>8,.0f}{maint:>9,.0f}{warr:>7,.0f}"
                  f"{s['op']*100:>5.1f}%{s['5']*100:>6.1f}%{s['5m']*100:>6.1f}%{s['8']*100:>6.1f}%{s['8m']*100:>6.1f}%"
                  f"{s['5mLLM']*100:>8.1f}%")
        # vendor-integrated variant: no warranty self-insurance (vendor DLC with system warranty, e.g. 3 y)
        inst, boxes, _ = installed("PRO6K4", n)
        maint, _ = yearly_cost("PRO6K4", n, retrofit=False)
        a, t = work_per_kwh("PRO6K4")
        mix = list_value(a, t)[2]
        print(f"  PRO6K4 as vendor DLC (no warranty self-insurance): 5y+m {share(op, inst, run_h, 5, mix, maint)*100:.1f}%, "
              f"8y+m {share(op, inst, run_h, 8, mix, maint)*100:.1f}%")
        for cc in ("low", "high"):
            inst_c, _, _ = installed("PRO6K4", n, cc)
            maint_c, warr_c = yearly_cost("PRO6K4", n, True, cc)
            print(f"  PRO6K4 cost {cc:<7}: {inst_c:>9,.0f} CHF, 5y+m {share(op, inst_c, run_h, 5, mix, maint_c, warr_c)*100:.1f}%")
        for pc in ("low", "high"):
            inst_c, _, _ = installed("PRO6K4", n)
            maint_c, warr_c = yearly_cost("PRO6K4", n)
            mix_p = list_value(a, t, pc)[2]
            print(f"  PRO6K4 price {pc:<6}: 5y+m {share(op, inst_c, run_h, 5, mix_p, maint_c, warr_c)*100:.1f}%")
        # B200LC: price at which the 5-y share (incl. maint) equals PRO6K4's
        target = res[(n, "PRO6K4")][1]["5m"]
        mix_b = list_value(b_a, b_t)[2]
        boxes_b = n / (B200LC["llama_w"] / 1000)
        house_fixed = mc.HOUSE_INTEGRATION["central"] + sum(house_items().values())
        maint_b = SERVICE_H * SERVICE_CHF_H + COOLANT_CHF
        budget = (target * mix_b - op - maint_b / run_h) * 5 * run_h - house_fixed
        print(f"  B200LC: {boxes_b:.2f} boxes per house; it matches PRO6K4's 5y+m share only if one SR780a V3 costs "
              f"<= {budget/boxes_b:,.0f} CHF incl. VAT (no public price found)")

    print("\n== 3. Realism column if the outlet temperature differs (r5_chain.sim, tank loss 2.80, N=6 / N=8) ==")
    print("  inlet limit -> house top / return limit: 40 C -> 45/35; 45 C -> 50/40 (plan); 50 C -> 55/45 (DLC50T; r5's DLC50"
          " keeps a 50 C top); 55 C -> 60/50 (outlet ~65 C, above the 60 C block ratings: JetCool-class plates only)")
    houses = ["underfloor 35/28", "radiator 50/40", "radiator 55/45", "radiator 70/55"]
    print(f"  {'chain':<7}{'house':<18}{'cov N=6':>8}{'cov N=8':>8}{'Jun-Aug':>8}{'util6':>7}{'stop h':>7}{'BEcase':>8}{'BEchg':>8}")
    for ch in ("DLC40", "DLC45", "DLC50", "DLC50T", "DLC55"):
        for h in houses:
            a6 = rc.sim(rows, 6, ch, h, tank_loss=rc.LOSS)
            a8 = rc.sim(rows, 8, ch, h, tank_loss=rc.LOSS)
            print(f"  {ch:<7}{h:<18}{a6['cov_srv']*100:>7.1f}%{a8['cov_srv']*100:>7.1f}%{a6['summer']*100:>7.1f}%"
                  f"{a6['util']*100:>6.1f}%{a6['blocked_h']:>7}{a6['be_case']:>8.4f}{a6['be_chg']:>8.4f}")
    print("  case column (baseline_sweep): " + " / ".join(f"{bs.simulate(rows, n)['coverage']*100:.1f}%" for n in (6, 8)))


if __name__ == "__main__":
    main()

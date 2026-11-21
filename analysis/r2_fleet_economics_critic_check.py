"""Round 2 critic check on analysis/r2_fleet_economics.py (imports it, changes nothing).

    python3 analysis/r2_fleet_economics_critic_check.py

Tests how the headline "N* = 1 at the Salad RTX 4090 average" moves when
(a) Salad uses only ONE GPU per machine (support.salad.com article 78), so a 1 kW
    of wall power holds fewer than 2 paid cards, and each card needs its own host;
(b) the rented GPU is not at full load (income per kWh of heat unchanged, but
    the machine then delivers less heat per paid hour -> modelled as income per kW-hour up, not done here);
(c) a yearly fixed cost per server (internet, maintenance; ASSUMPTION values) is added.
All host-power and fixed-cost values below are ASSUMPTIONS, marked as such.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from baseline_sweep import load  # noqa: E402
from r2_fleet_economics import ranks, margin, USD, SALAD_4090, BE_CREDIT  # noqa: E402

rks = ranks(load())
CARD_CHF = 2338.0 * USD          # round-1 sourced card price
HOST_CHF = 2000.0                # round-1 ASSUMPTION, per host machine
print("Salad RTX 4090 host rates; one GPU per machine; 450 W card + host W (ASSUMPTION); life 5 y; heat credited; 100% sold")
print(f"{'host W':>7} {'cards/kW':>9} {'hw CHF/kW':>10} | {'rate':>6} {'CHF/kWh-h':>10} {'rank1 margin':>13} {'payback y':>10} {'N*':>3}")
for host_w in (100, 150, 200):
    per_kw = 1000.0 / (450 + host_w)
    hw = (CARD_CHF + HOST_CHF) * per_kw
    for name in ("avg", "top25", "max"):
        p = SALAD_4090[name] * per_kw * USD
        n = 0
        for rk in rks:
            m = margin(rk, p)
            if m > 0 and hw / m <= 5:
                n = rk["k"]
            else:
                break
        m1 = margin(rks[0], p)
        print(f"{host_w:>7} {per_kw:>9.2f} {hw:>10,.0f} | {name:>6} {p:>10.3f} {m1:>13,.0f} {(hw / m1 if m1 > 0 else float('inf')):>10.1f} {n:>3}")

print("\nInvestigator's own case (2 cards per kW in ONE machine, 5,924 CHF), Salad average, plus a fixed yearly cost per server (ASSUMPTION):")
p = SALAD_4090["avg"] * 2.0 * USD
for fixed in (0, 100, 300, 600):
    m1 = margin(rks[0], p) - fixed
    print(f"  fixed {fixed:>4} CHF/yr: rank-1 margin {m1:>6,.0f} CHF/yr, payback {5924 / m1:>5.1f} y, net after 5-y straight-line hardware {m1 - 5924 / 5:>6,.0f} CHF/yr")

print("\nBreak-even per SOLD hour if the server STOPS when it has no paying job (heat credited): "
      f"{BE_CREDIT:.4f} CHF at any sold share (coverage falls instead); the 0.283 / 0.452 CHF figures hold only if unsold hours still draw 1 kW.")

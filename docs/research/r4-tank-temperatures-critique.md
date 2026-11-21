# Critique, round 4: tank temperatures (r4-tank-temperatures.md)

Critic role: a sceptical DigitalHeat founder. Plan and assessment only. No existing file was changed, git state was not touched, and 0 Firecrawl calls were made. Currency: CHF, using the case constants in `analysis/baseline_sweep.py` (0.3325 CHF/kWh; heat valued at 0.133 CHF/kWh). No conversion was needed.

## 1. Verdict in one paragraph

The sources check out. The script reproduces its own output exactly, and its case mode matches `baseline_sweep.simulate()`. The underfloor realism column (77.6% / 90.6%, June–August 82.2%) holds. The temperature chain has one internal error, though, and it changes the radiator results and the pitch sentence.

The investigator takes server coolant at **45 °C in and 55 °C out** (NVIDIA) and a **5 K CDU approach** (Lenovo Gold: TCS 45–50 °C against FWS 40–45 °C). The 5 K is the *cold-end* approach: water going to the servers is at least 5 K warmer than the house water coming back to the CDU. If the servers take 45 °C, the house return to the CDU must be **≤ 40 °C, not ≤ 45 °C** as section 3 of the research file says.

A 55/45 radiator house returns above 40 °C in 853 heating hours. In those hours the servers cannot be cooled to spec. If the servers stop in those hours, the "radiator 55/45" column falls from **77.4% / 90.4% to 64.3% / 73.0%** (N=6 / N=8, with tank loss). The 70/55 "about 59%" falls to **about 30%**. So the pitch sentence "enough for … radiators sized for 55 °C" is not supported. Radiators sized for **50/40** (the Swiss limit for new or replaced emitters) and floor heating pass the check with no loss.

## 2. Source checks (all opened by me, 2026-11-21)

| Claim | URL opened | What I read | Verdict |
|---|---|---|---|
| C1, C2 | https://merkblatt.suissetec.ch/de-CH/HEIZ111/file/HEIZ111.pdf (pdftotext) | "info Mai 2011"; "Seit dem 4. April 2008 sind die … MuKEn in Kraft"; limits for "neue oder ersetzte Wärmeabgabesysteme bei der tiefsten Aussentemperatur (gemäss SIA-Norm)": Fussbodenheizungen max. 35 °C, Radiatoren max. 50 °C; Rücklauf "z. B. 28 °C"; "Region Zürich − 8 °C"; at +5 °C, mean heating water "ca. 28 °C" | Confirmed. Caveat: the limit applies only to **new or replaced** emitters, so existing radiator houses are not bound by it |
| C3, C4 | https://merkblatt.suissetec.ch/de-CH/ALLE222/file/ALLE222.pdf (pdftotext) | "Februar 2025"; without warm-held pipes the station outlet is "mindestens 52 °C"; with them, calculated 58–60 °C, pipes ≥ 55 °C; supply "2 bis 5 K über der Warmwassertemperatur"; return "möglichst mit tiefer Temperatur"; also "tiefere Temperaturen bei Frischwasserstationen nicht mehr möglich" | Confirmed. The last sentence makes C28 (a 47 °C station feeding a cylinder) a real compliance question |
| C5 | https://blogs.nvidia.com/blog/liquid-cooling-ai-factories/ (curl) | published 2026-06-22T05:00 UTC (page shows June 21, 2026); "the coolant entering a fully liquid-cooled chip at 45 degrees Celsius exits at roughly 55 degrees"; the context is **Rubin** rack-scale AI infrastructure | Confirmed. Caveat: it describes a rack-scale AI platform, not a 1 kW basement rack server, and says "roughly" |
| C6 | https://lenovopress.lenovo.com/lp2018-lenovo-neptune-direct-water-cooling-standards (curl) | Table 1, Gold: "FWS Temperature 40°C to 45°C", "TCS Secondary Temperature 45°C to 50°C"; W-number = "upper bound of the inlet fluid temperature"; no outlet temperature or ΔT found | Confirmed |
| C9 | https://www.sbz-monteur.de/sites/default/files/sbzm_pdf/file_226319.pdf (pdftotext) | "SBZ Monteur 2008 / 12"; 49,83; "Der Exponent … beträgt 1,3"; 70/55 low-temperature boiler, 55/45 condensing boiler; 35/28 for a very well insulated new house with a heat pump; 19,95% at 35/28/22 | Confirmed |

## 3. Re-runs

- `python3 analysis/r4_tank_layout.py`: exit 0, output identical to section 5 of the research file. The regression check prints OK for N=6 and N=8.
- C25, run from `analysis/`: `simulate(rows, n, dhw_direct_share=37/45, tank=…)` gives N=6: 78.04% (tank 35 and 34.9), 77.72% with 2.80 loss; N=8: 91.02%, 90.74% with loss. Break-even 0.2261 / 0.2292 / 0.2293. Matches the research file.
- C15: on `curve()`, supply exceeds 50 °C up to −1.2 °C for 55/45 and up to +6.4 °C for 70/55. Matches "below −1.1" and "below +6.5".
- C27: `curve(15/25.6, underfloor 35/28)` gives 29.1/25.0, mean 27.07 °C. Matches.

## 4. The main error: house return limit at the CDU

The chain as stated: server inlet 45 °C → outlet about 55 °C → CDU with 5 K approach → house side 50 °C. With a counter-flow plate exchanger, the house *supply* (50) sits 5 K below the server outlet (55), and the server *inlet* (45) sits 5 K above the house *return*. So the **house return must be ≤ 40 °C**. Lenovo's table says the same thing: FWS (house return) 40 °C ↔ TCS (to servers) 45 °C. The research file reads FWS 45 °C as the limit, but that pairs with a 50 °C server inlet, about 60 °C outlet and a 55 °C house loop. That is a different, warmer operating point that NVIDIA's "up to 45 °C" does not support.

In space-heating hours the bottom of the buffer, where the CDU draws from, sits at the heating return temperature. The fresh-water station return is cold but small: 0.5 kWh/h against several kWh/h of space heat. So in hours when the heating return is above 40 °C the servers cannot be cooled to spec. They have to stop, throttle, or dump heat through a dry cooler.

Scratch check (in my scratchpad, not in the repo; the code is listed below so anyone can re-run it). It copies the investigator's `sim()` logic and sets k = 0 in space-heating hours whose return temperature exceeds `ret_max`:

```
N  system            ret_max  coverage  util   blocked_h  demand_in_blocked_h
6  underfloor 35/28      40     78.0%   57.9%       0          0
6  radiator 50/40        40     77.9%   57.8%       0          0
6  radiator 55/45        99     77.8%   57.8%       0          0      (= investigator)
6  radiator 55/45        40     64.7%   48.0%     853       7431
6  radiator 70/55        99     59.2%   44.1%       0          0      (= investigator)
6  radiator 70/55        45     50.0%   37.1%    1762      14067
6  radiator 70/55        40     29.5%   21.9%    3188      22485
8  radiator 55/45        40     73.4%   40.9%     853       7431
8  radiator 70/55        40     31.2%   17.4%    3188      22485
12 radiator 55/45        40     76.9%   28.6%     853       7431
12 radiator 70/55        40     32.2%   12.0%    3188      22485
with loss 2.80: N=6 underfloor ret_max 40: 77.6% (unchanged)   N=8: 90.6% (unchanged)
with loss 2.80: N=6 radiator 55/45 ret_max 40: 64.3%            N=8: 73.0%
```

Reading the check: k = 0 is the pessimistic bound and the investigator's figure is the optimistic bound. Where the truth lies depends on the server's real maximum inlet temperature, which no datasheet in the plan gives. Either way, "55 °C radiators are fine" cannot go on a slide. "Floor heating or radiators sized for 50 °C" can, because both pass with zero blocked hours.

Scratch script (run as `python3 <path>/r4tankcrit_check.py`, standard library only, imports `analysis/r4_tank_layout.py` without changing it):

```python
import sys
sys.path.insert(0, "/Users/saif/Work/digitalheat/analysis")
import r4_tank_layout as m
from baseline_sweep import load

def sim_ret(rows, n, sysdef, ret_max, tank_loss=0.0, t_top=m.T_TOP):
    cap = m.C_KWH_PER_K * (t_top - 20.0)
    s_dhw = m.dhw_share(t_top, 55.0)
    soc = used = run_h = dem = 0.0
    blocked_h = 0; blocked_dem = 0.0
    for t, sh, hw in rows:
        dem += sh + hw
        soc -= min(soc, tank_loss / 24.0)
        if sh > 0:
            ts, tr = m.curve(sh / 10.0, sysdef)
            s_sh = m.sh_share(ts, tr, t_top)
            floor_e = m.C_KWH_PER_K * max(0.0, tr - 20.0)
        else:
            tr, s_sh, floor_e = 20.0, 1.0, 0.0
        d_sh, d_hw = sh * s_sh, hw * s_dhw
        nmax = n
        if sh > 0 and tr > ret_max + 1e-9:
            nmax = 0; blocked_h += 1; blocked_dem += sh + hw
        def step(k, s):
            heat = k * m.Q1
            a = min(d_sh, heat); heat -= a
            b = min(d_hw, heat); heat -= b
            c = min(d_sh - a, max(0.0, s - floor_e)); s -= c
            e = min(d_hw - b, s); s -= e
            return a + b + c + e, s + heat
        k = 0
        for kk in range(nmax, -1, -1):
            if step(kk, soc)[1] <= cap + 1e-9:
                k = kk; break
        u, soc = step(k, soc)
        used += u; run_h += k
    return used / dem, run_h / (n * 8760), blocked_h, blocked_dem
```

## 5. Other weaknesses

1. **The hot-water cylinder's own standby loss is missing.** In layout A a small drinking-water cylinder is held at 55 °C by an electric element. Preheated water enters only during draws, so the element also covers the cylinder's standby loss all year. That loss is not in `boost_el` (779 kWh/yr). For a 150–200 l cylinder it could be several hundred kWh/yr (*assumption*, not sourced). This does not change coverage under the case convention, but it moves the "element charged to the servers" break-even (C20), and it is a real operating cost. A heat-pump house would have a cylinder too, so whether to charge it to the servers is a convention question. It should be stated.
2. **"Fully mixed" is not what 6b models.** The `floor_mode="supply"` variant only raises the space-heating draw floor. Hot water is still preheated to 47 °C from a 50 °C top, and the capacity is unchanged. A truly mixed tank would also lower the hot-water preheat temperature. C24's "at most 0.2 points" holds only for what was actually modelled.
3. **Break-even does not respond to temperature by construction.** Under the follow rule nothing is dumped, so the case-convention break-even moves only with tank loss (+0.003). C19 must not be read as "temperatures cost only 0.003 CHF".
4. **0 kWh dumped is by construction, and in the 70/55 house and the cold hours of the 55/45 house it is not physical.** Servers that cannot be cooled must dump or stop. The model does neither.
5. **The 45 °C loop sensitivity (C22) keeps the return limit implicit.** At a 45 °C house side the return limit would be about 35 °C, so radiator houses would lose even more than the 10.6 points shown.
6. **Scale mismatch of the 55 °C source.** NVIDIA's figure is for Rubin rack-scale AI systems with a CDU. A home installation of 6–8 one-kilowatt servers would need its own small CDU, and no small-scale datasheet is cited.
7. **The pitch sentence is too long for a 5-minute pitch** (four sentences plus a footnote), and it quotes the 55/45 figure (77.4%) that section 4 shows is optimistic.

## 6. What survives for the plan

- Default reference-house figures stay on the case assumptions (no change).
- **Realism column:** `dhw_direct_share = 0.822` plus `tank_loss_kwh_day = 2.80`, both already in `baseline_sweep`. Labelled "floor heating or radiators sized ≤ 50 °C": 77.6% / 90.6%, June–August 82.2%, break-even 0.2293 (case convention). No new build scope.
- **"Where it stops holding":** a 55/45 radiator house reaches 64–77% at N=6 and 73–90% at N=8, depending on the servers' maximum inlet temperature. A 70/55 house reaches at most 59%, and about 30% if the servers need return water ≤ 40 °C. A 45 °C loop drops June–August to 71%.
- **Suggested pitch sentence:** "Our headline uses the case's simplifications. Real servers deliver about 50 °C: enough for floor heating and new radiators, but hot water needs a small electric top-up, so summer coverage drops from 100% to 82% and the year from 79.6% to 77.6% at six servers. Old radiator houses are where it stops working."

"""Site and scheduler studies for the business case. One command, all numbers reproducible:

    python3 scripts/site_studies.py      # writes outputs/site_studies.md, outputs/site_studies.json, plots/*.png

 1. Daily curves: homes (morning/evening) vs businesses (office hours) vs pharma (shifts + 24/7),
    and how much flatter the combined fleet is than each site alone.
 2. Household size: why 4-5 person families are the target (hot water = the summer heat sink).
 3. Summer: the services fleet with and without partial power and a dry cooler.
 4. Seasons: heat-useful capacity per month, and simulation work deferred to winter.
 5. Redundancy: an outage with and without the twin (2-site) tier.

Uses only the scheduler package (same code as the yearly balance); matplotlib for the plots.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scheduler.balance import SERVICES, run  # noqa: E402
from scheduler.core import service_job_types  # noqa: E402
from scheduler.sites import Site, demand, weekdays  # noqa: E402
from scheduler.weather import temperatures  # noqa: E402

OUT = ROOT / "outputs"
PLOTS = ROOT / "plots"
INK, RUST, AMBER, TEAL, PAPER = "#141412", "#c0653a", "#f2a65a", "#5fa8b0", "#e8e4da"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def site(kind, **kw):
    d = dict(id=kind, kind=kind, lat=47.56, lon=7.59)
    d.update(kw)
    return Site.from_dict(d)


def daily_curves():
    """Mean weekday profile per site kind in January and July, normalised to the site's own daily mean."""
    temps = temperatures(47.56, 7.59, 2025)
    wd = weekdays(2025)
    kinds = ["family", "office", "pharma", "hospital", "spa"]
    res = {}
    for k in kinds:
        dem = demand(site(k), temps)
        res[k] = {}
        for name, days in (("January", range(0, 31)), ("July", range(181, 212))):
            work = [d for d in days if wd[d] < 5]
            prof = [sum(dem[d * 24 + h] for d in work) / len(work) for h in range(24)]
            res[k][name] = [round(x, 3) for x in prof]
    return res


def complementarity(curves):
    """Peak-to-mean of each site and of a mix scaled to equal daily energy (January weekdays)."""
    out = {}
    for month in ("January", "July"):
        norm = {}
        for k, v in curves.items():
            m = sum(v[month]) / 24
            norm[k] = [x / m for x in v[month]] if m else v[month]
        single = {k: round(max(v), 2) for k, v in norm.items()}
        mix = [sum(norm[k][h] for k in ("family", "office")) / 2 for h in range(24)]
        mix3 = [sum(norm[k][h] for k in ("family", "office", "pharma")) / 3 for h in range(24)]
        out[month] = {"peak_to_mean": single, "family+office": round(max(mix), 2),
                      "family+office+pharma": round(max(mix3), 2)}
    return out


def household_sizes():
    rows = []
    for p in (1, 2, 3, 4, 5):
        s = dict(id=f"F{p}", kind="family", name=f"{p} people", lat=47.56, lon=7.59, size=p)
        f = run([s], 2025, series=False)
        y = f["fleet"]
        summer = sum(m["demand"] for m in f["monthly"][3:9])
        rows.append({"people": p, "summer_heat_kwh": summer, "annual_heat_kwh": y["demand_kwh"],
                     "coverage": y["coverage"], "utilisation": y["utilisation"],
                     "summer_utilisation": y["summer_utilisation"], "break_even": y["break_even_chf_per_server_h"]})
    return rows


def summer_options():
    types = service_job_types()
    cases = {
        "base (on/off servers)": dict(),
        "partial power": dict(partial=True),
        "dry cooler 4 kW per site, deadline/forced only": dict(cool=4.0),
        "dry cooler 4 kW per site, fill spare servers": dict(cool=4.0, cool_fill=True),
    }
    out = {}
    for name, c in cases.items():
        sites = [dict(s, drycooler_kw=c.get("cool", 0.0)) for s in SERVICES]
        r = run(sites, 2025, series=False, types=types, partial=c.get("partial", False),
                cool_fill=c.get("cool_fill", False))
        f = r["fleet"]
        out[name] = {k: f[k] for k in ("coverage", "dumped_kwh", "utilisation", "summer_utilisation", "missed_pct",
                                       "cooled_server_h", "fan_kwh", "always_on_share", "electricity_chf",
                                       "heat_value_chf", "run_server_h", "break_even_chf_per_server_h")}
        if name == "base (on/off servers)":
            out["_monthly"] = r["monthly"]
            out["_sites"] = [{"id": s["id"], "name": s["name"], "servers": s["servers"], **{
                k: s["year"][k] for k in ("coverage", "utilisation", "summer_utilisation", "demand_kwh")}}
                for s in r["sites"]]
    return out


def outage_study(n=100, hours=12, seed=7):
    """n random single-site outages of `hours` h over the year (fixed seed), twin tier off and on."""
    import random
    rnd = random.Random(seed)
    outs = [(rnd.choice(SERVICES)["id"], rnd.randrange(365), hours, rnd.randrange(24)) for _ in range(n)]
    out = {"outages": outs}
    for r_ in (1, 2):
        r = run(SERVICES, 2025, series=False, types=service_job_types(replicas=r_), outages=outs)
        out[f"replicas={r_}"] = {"lost_server_h": r["lost_server_h"], "twin": r["jobs_by_type"]["twin"],
                                 "sim": r["jobs_by_type"]["sim"], "missed_pct": r["fleet"]["missed_pct"]}
    return out


def partial_power_house():
    """Reference house alone: hours with a server on, on/off vs partial power."""
    from scheduler.balance import REFERENCE
    out = {}
    for name, p in (("on/off", False), ("partial power", True)):
        r = run(REFERENCE, 2025, series=True, partial=p)
        on = r["series"][0]["running"]
        summer = range(90 * 24, 273 * 24)
        out[name] = {"on_share": r["fleet"]["always_on_share"],
                     "summer_on_share": round(sum(1 for t in summer if on[t] > 0) / len(summer), 4),
                     "coverage": r["fleet"]["coverage"], "utilisation": r["fleet"]["utilisation"],
                     "switches": sum(1 for t in range(1, len(on)) if (on[t] > 0) != (on[t - 1] > 0))}
    return out


def plots(curves, seasons):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    PLOTS.mkdir(exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    colors = {"family": RUST, "office": INK, "pharma": TEAL, "hospital": AMBER, "spa": "#8a8577"}
    labels = {"family": "Family home (5)", "office": "Office", "pharma": "Pharma lab", "hospital": "Hospital",
              "spa": "Spa & pool"}
    for ax, month in zip(axes, ("January", "July")):
        for k in ("family", "office", "pharma"):
            v = curves[k][month]
            m = sum(v) / 24
            ax.plot(range(24), [x / m for x in v], color=colors[k], lw=2, label=labels[k])
        ax.set_title(f"{month} weekday, demand ÷ daily mean", fontsize=10, loc="left")
        ax.set_xticks([0, 6, 12, 18, 23])
        ax.set_xlabel("hour")
        ax.grid(alpha=0.25)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(PLOTS / "daily_profiles.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 3.6))
    cap = [m["permit_sh"] for m in seasons]
    q = [m["queue_sh"] for m in seasons]
    ax.bar(MONTHS, cap, color=AMBER, label="heat-useful capacity (server-h)")
    ax.set_ylabel("server-h per month")
    ax2 = ax.twinx()
    ax2.plot(MONTHS, q, color=RUST, lw=2.5, marker="o", label="simulation work deferred (server-h)")
    ax2.set_ylabel("deferred server-h", color=RUST)
    ax.set_title("Services fleet 2025: capacity drops in summer, simulations wait for autumn", fontsize=10, loc="left")
    for a in (ax, ax2):
        a.spines["top"].set_visible(False)
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    fig.tight_layout()
    fig.savefig(PLOTS / "seasonal_capacity.png", dpi=150)
    plt.close(fig)


def pct(x):
    return f"{100 * x:.1f} %"


def report(r):
    L = ["# Site and scheduler studies", "",
         "Generated by `python3 scripts/site_studies.py` (Basel weather 2025, same scheduler as the yearly "
         "balance). Scenario numbers, not measurements. The reference-house key figures are unchanged by "
         "everything here.", ""]
    L += ["## 1. Daily curves: homes vs businesses", "",
          "Mean weekday profile ÷ the site's own daily mean (1.00 = flat). Plot: `plots/daily_profiles.png`.", "",
          "| Site | Jan peak/mean | Jul peak/mean | Peak hours (Jan) |", "|---|---|---|---|"]
    for k, v in r["curves"].items():
        jan = v["January"]
        top = sorted(range(24), key=lambda h: -jan[h])[:3]
        L.append(f"| {k} | {r['complementarity']['January']['peak_to_mean'][k]:.2f} | "
                 f"{r['complementarity']['July']['peak_to_mean'][k]:.2f} | {', '.join(f'{h:02d}h' for h in sorted(top))} |")
    c = r["complementarity"]
    L += ["", f"Equal-energy mix in January: family + office peak/mean **{c['January']['family+office']:.2f}**, "
          f"family + office + pharma **{c['January']['family+office+pharma']:.2f}**; "
          f"July: {c['July']['family+office']:.2f} and {c['July']['family+office+pharma']:.2f}. "
          "Measured profiles (BDEW) show homes and offices both boost at 06-08. They complement each other "
          "afterwards: homes have a second peak 17-21 h when offices are in setback, offices hold the daytime when "
          "homes dip, and offices drop at weekends while homes do not. Mixing just the two flattens the peak only a "
          "little; adding a 24/7 site (pharma reheat, hospital, spa) flattens it more. The larger complement is "
          "seasonal: sites with summer heat (pharma, spa, hospital) keep servers busy when homes and offices do not "
          "(section 3).", ""]
    L += ["## 2. Household size", "",
          "Family home, same building (case formula), 4 servers, 35 kWh tank; only the number of people changes "
          "(3 kWh hot water per person and day).", "",
          "| People | Summer heat Apr-Sep (kWh) | Year (kWh) | Covered | Utilisation | Summer util. | Break-even CHF/server-h |",
          "|---|---|---|---|---|---|---|"]
    for h in r["households"]:
        L.append(f"| {h['people']} | {h['summer_heat_kwh']:,} | {h['annual_heat_kwh']:,} | {pct(h['coverage'])} | "
                 f"{pct(h['utilisation'])} | {pct(h['summer_utilisation'])} | {h['break_even']:.3f} |")
    L += ["", "Hot water is the only summer heat sink in a home, so it scales with the number of people: a family "
          "of five keeps the servers about three times as busy in summer as a single person.", ""]
    L += ["## 3. Summer options on the services fleet", "",
          "| Option | Covered | Dumped (kWh) | Util. | Summer util. | Missed | Cooled server-h | Fan kWh | ≥1 server on | Break-even |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for k, v in r["summer"].items():
        if k.startswith("_"):
            continue
        L.append(f"| {k} | {pct(v['coverage'])} | {v['dumped_kwh']:,.0f} | {pct(v['utilisation'])} | "
                 f"{pct(v['summer_utilisation'])} | {v['missed_pct']:.2f} % | {v['cooled_server_h']:,.0f} | "
                 f"{v['fan_kwh']:,.0f} | {pct(v['always_on_share'])} | {v['break_even_chf_per_server_h']:.3f} |")
    L += ["", "Sites of the services fleet (base case):", "", "| Site | Servers | Heat demand (kWh) | Covered | Util. | Summer util. |",
          "|---|---|---|---|---|---|"]
    for s in r["summer"]["_sites"]:
        L.append(f"| {s['name']} | {s['servers']} | {s['demand_kwh']:,} | {pct(s['coverage'])} | "
                 f"{pct(s['utilisation'])} | {pct(s['summer_utilisation'])} |")
    L += ["", "## 4. Seasons: capacity and deferred simulations", "",
          "Heat-useful capacity = server-h whose heat the sites can use (heat permit). Simulations (8 server-h, "
          "due in 120 days, 100 a day) wait when there is no heat. Plot: `plots/seasonal_capacity.png`.", "",
          "| Month | Capacity (server-h) | Capacity % of servers | Ran | Simulation + twin ran | Deferred at month end (server-h) | Jobs waiting |",
          "|---|---|---|---|---|---|---|"]
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    n = sum(s["servers"] for s in r["summer"]["_sites"])
    for i, m in enumerate(r["summer"]["_monthly"]):
        L.append(f"| {MONTHS[i]} | {m['permit_sh']:,.0f} | {100 * m['permit_sh'] / (n * days[i] * 24):.0f} % | "
                 f"{m['run_sh']:,.0f} | {m['by_type']['other']:,.0f} | {m['queue_sh']:,.0f} | {m['queue_jobs']} |")
    ph = r["partial_house"]
    L += ["", "Partial power on the reference house alone (power capping 30-100 %, throughput taken as proportional "
          "to power):", "", "| Mode | Hours with a server on | Summer hours on | On/off switches | Covered | Util. |",
          "|---|---|---|---|---|---|"]
    for k, v in ph.items():
        L.append(f"| {k} | {pct(v['on_share'])} | {pct(v['summer_on_share'])} | {v['switches']:,} | "
                 f"{pct(v['coverage'])} | {pct(v['utilisation'])} |")
    o = r["outage"]
    L += ["", "## 5. Redundancy under outages", "",
          f"{len(o['outages'])} random single-site outages of {o['outages'][0][2]} h over 2025 (seed 7), same "
          "outages for both runs. Work held on a site that goes down is lost back to the last copy elsewhere.", "",
          "| Twin tier | Work lost (server-h) | Twin jobs done | Twin copies lost, job carried by its other copy | "
          "Twin jobs restarted from zero | Sim jobs restarted | Missed |",
          "|---|---|---|---|---|---|---|"]
    for k, v in o.items():
        if k == "outages":
            continue
        L.append(f"| {k} | {v['lost_server_h']:.1f} | {v['twin']['done']} | {v['twin']['lost']} | "
                 f"{v['twin']['restarts']} | {v['sim']['restarts']} | {v['missed_pct']:.2f} % |")
    L.append("")
    return "\n".join(L)


def main():
    curves = daily_curves()
    r = {"curves": curves, "complementarity": complementarity(curves), "households": household_sizes(),
         "summer": summer_options(), "outage": outage_study(), "partial_house": partial_power_house()}
    OUT.mkdir(exist_ok=True)
    (OUT / "site_studies.json").write_text(json.dumps(r, indent=1))
    (OUT / "site_studies.md").write_text(report(r))
    plots(curves, r["summer"]["_monthly"])
    print(report(r))


if __name__ == "__main__":
    main()

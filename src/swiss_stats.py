"""Annual statistics per location (Part A2) and climate zones (Part B3).

Definitions (all for calendar year 2025, local days in Europe/Zurich):
- heating_days        days with mean temperature_2m < 12 degC (case rule)
- hgt_20_12           Swiss/German heating degree days HGT 20/12, in Kd: sum over heating days of
                      (20 - daily mean). Same 12 degC limit as the case, so this is our main HDD.
- hdd_18_15           Eurostat convention, in Kd: sum over days with mean <= 15 degC of (18 - daily mean).
- winter = Jan-Mar and Oct-Dec 2025, summer = Apr-Sep 2025 (both inside the calendar year).
- Two house sizings: "case" uses 25.6 everywhere (Basel 2025); "local" uses 20 minus the
  location's own coldest hour, so every house peaks at 10 kW.
- Server counts divide heat by the recoverable heat per server (0.8 kW; sensitivity 0.85 kW):
    *_servers_mean  = mean demand in the season / recovery   (needs storage to shift heat within the day)
    winter_servers_firm = lowest DAILY mean demand in the core winter (Dec-Feb) / recovery
    summer_servers_firm = lowest DAILY mean demand in Apr-Sep / recovery
                      (servers that could run 24 h on every one of those days without dumping heat,
                       assuming the 35 kWh tank evens out the hours within a day). Oct, Nov and Mar
                       are left out of the "firm" winter number because they always contain warm days.
"""

import pandas as pd

from src.load_data import HOT_WATER_KWH_PER_DAY

RECOVERY = {"80": 0.8, "85": 0.85}
WINTER_MONTHS = [1, 2, 3, 10, 11, 12]
CORE_WINTER_MONTHS = [12, 1, 2]

# Climate zones by HGT 20/12 (Part B3). Boundaries are DERIVED from "server-years": the number of
# servers whose heat a reference house (case sizing) could absorb if heat could be stored across the
# whole year. annual demand ~= 9.375 * HGT + 4,380 kWh, and one server at 0.8 kW gives 7,008 kWh/year.
# The choice of whole server-years (4, 5, 6) as boundaries is an ASSUMPTION; see docs/criteria.md.
ZONES = [  # (name, HGT upper bound in Kd)
    ("warm", 2520),
    ("mild", 3270),
    ("cold", 4020),
    ("very cold", float("inf")),
]


def zone_for(hgt):
    return next(name for name, upper in ZONES if hgt < upper)


def location_stats(name, df):
    """Annual numbers for one location from its hourly table (output of swiss_points.load_all)."""
    month = df.timestamp.dt.month
    winter, summer = df[month.isin(WINTER_MONTHS)], df[~month.isin(WINTER_MONTHS)]
    daily = df.groupby("date").agg(mean_t=("day_mean_temperature_2m", "first"), heat=("heating_day", "first"))
    coldest = df.loc[df.temperature_2m.idxmin()]
    out = {
        "name": name,
        "mean_temp_c": df.temperature_2m.mean(),
        "winter_mean_temp_c": winter.temperature_2m.mean(),
        "summer_mean_temp_c": summer.temperature_2m.mean(),
        "coldest_c": coldest.temperature_2m,
        "coldest_time": coldest.timestamp.strftime("%Y-%m-%d %H:%M"),
        "heating_days": int(daily.heat.sum()),
        "summer_heating_days": int(daily[pd.to_datetime(daily.index).month.isin(range(4, 10))].heat.sum()),
        "hgt_20_12": float((20 - daily.mean_t[daily.mean_t < 12]).sum()),
        "hdd_18_15": float((18 - daily.mean_t[daily.mean_t <= 15]).sum()),
        "hot_water_kwh": df.hot_water_kwh.sum(),
        "summer_hot_water_kwh": summer.hot_water_kwh.sum(),
    }
    for variant, space_col, demand_col in [("case", "space_kwh", "demand_kwh"),
                                           ("local", "space_kwh_local", "demand_kwh_local")]:
        d = df[demand_col]
        day_mean = d.groupby(df.date).mean()
        day_month = pd.to_datetime(day_mean.index).month
        v = {
            "space_kwh": df[space_col].sum(),
            "demand_kwh": d.sum(),
            "summer_space_kwh": summer[space_col].sum(),
            "peak_kw": d.max(),
            "hours_over_5kw": int((d > 5).sum()),
            "winter_mean_kw": d[month.isin(WINTER_MONTHS)].mean(),
            "summer_mean_kw": d[~month.isin(WINTER_MONTHS)].mean(),
            "winter_min_day_kw": day_mean[day_month.isin(CORE_WINTER_MONTHS)].min(),
            "summer_min_day_kw": day_mean[~day_month.isin(WINTER_MONTHS)].min(),
        }
        for r_key, r in RECOVERY.items():
            v[f"winter_servers_mean_{r_key}"] = v["winter_mean_kw"] / r
            v[f"summer_servers_mean_{r_key}"] = v["summer_mean_kw"] / r
            v[f"winter_servers_firm_{r_key}"] = v["winter_min_day_kw"] / r
            v[f"summer_servers_firm_{r_key}"] = v["summer_min_day_kw"] / r
            v[f"peak_servers_{r_key}"] = v["peak_kw"] / r
            v[f"server_years_{r_key}"] = v["demand_kwh"] / (r * 8760)
        out.update({f"{k}_{variant}": val for k, val in v.items()})
    out["zone"] = zone_for(out["hgt_20_12"])
    return out


def all_stats(points, hourly):
    stats = pd.DataFrame([location_stats(n, hourly[n]) for n in points.name])
    return points.merge(stats, on="name")


def check_hot_water(stats):
    """Hot water is the same everywhere: 12 kWh x 365 days."""
    expected = HOT_WATER_KWH_PER_DAY * 365
    assert (stats.hot_water_kwh - expected).abs().max() < 1e-6, "hot water total is not 4,380 kWh everywhere"


# ------------------------------------------------------------------ monthly numbers
MONTHLY_FIELDS = ["mean_temp_c", "min_temp_c", "heating_days", "hgt_20_12", "hot_water_kwh"]
MONTHLY_SIZED = ["space_kwh", "demand_kwh", "mean_kw", "peak_kw", "min_day_kw"]


def monthly_stats(name, df):
    """One row per month (1-12) for one location. Same definitions as the annual numbers:

    - heating_days / hgt_20_12: days of that month (a day belongs to the month of its local date)
    - mean_kw: mean hourly demand in the month; min_day_kw: lowest daily mean demand in the month
    - servers_mean_<r>_<v> = mean_kw / recovery: servers whose heat the house absorbs on average
    - servers_firm_<r>_<v> = min_day_kw / recovery: servers that could run 24 h on every day of the month
      without dumping heat (assuming the 35 kWh tank evens out the hours of a day)
    """
    month = df.timestamp.dt.month
    daily = df.groupby("date").agg(mean_t=("day_mean_temperature_2m", "first"), heat=("heating_day", "first"))
    day_month = pd.to_datetime(daily.index).month
    rows = []
    for m in range(1, 13):
        h, d = df[month == m], daily[day_month == m]
        row = {"name": name, "month": m,
               "mean_temp_c": h.temperature_2m.mean(), "min_temp_c": h.temperature_2m.min(),
               "heating_days": int(d.heat.sum()), "hgt_20_12": float((20 - d.mean_t[d.mean_t < 12]).sum()),
               "hot_water_kwh": h.hot_water_kwh.sum()}
        for variant, space_col, demand_col in [("case", "space_kwh", "demand_kwh"),
                                               ("local", "space_kwh_local", "demand_kwh_local")]:
            dem = h[demand_col]
            day_mean = dem.groupby(h.date).mean()
            v = {"space_kwh": h[space_col].sum(), "demand_kwh": dem.sum(), "mean_kw": dem.mean(),
                 "peak_kw": dem.max(), "min_day_kw": day_mean.min()}
            for r_key, r in RECOVERY.items():
                v[f"servers_mean_{r_key}"] = v["mean_kw"] / r
                v[f"servers_firm_{r_key}"] = v["min_day_kw"] / r
            row.update({f"{k}_{variant}": val for k, val in v.items()})
        rows.append(row)
    return rows


def all_monthly(points, hourly):
    return pd.DataFrame([r for n in points.name for r in monthly_stats(n, hourly[n])])


def check_monthly(monthly, stats):
    """Monthly numbers must add up to the annual numbers."""
    sums = monthly.groupby("name")[["heating_days", "hgt_20_12", "space_kwh_case", "space_kwh_local", "demand_kwh_case"]].sum()
    s = stats.set_index("name").loc[sums.index]
    for col in sums.columns:
        diff = (sums[col] - s[col]).abs().max()
        assert diff < 1e-6, f"monthly {col} does not add up to the annual value (max diff {diff})"

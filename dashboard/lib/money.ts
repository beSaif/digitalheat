/*
 * Year economics of one house, the same formulas as money() in scripts/build_fleet_scenario.py.
 * The generator writes defaults (site.money); this module recomputes them when the operator moves
 * the selling price, occupancy or who keeps the heat.
 *
 *   electricity  = sold server-h × 1 kW × electricity price
 *   heat value   = heat actually used × electricity price / COP 2.5 × heat share     (case rule at share 1)
 *   break-even   = (electricity − heat value) / sold server-h
 *   hardware/yr  = installed / life + maintenance + card failures + insurance + uplink   (no interest)
 *   price needed = (hardware/yr + electricity − heat value) / sold server-h
 */
import { nf, type Economics, type Fleet, type Site } from "./data";

export type Assumptions = {
  price: number; // CHF per sold server-hour
  occupancy: number | null; // share of heat-permitted hours sold; null = as simulated
  heatShare: number; // 1 = operator is credited the heat (case formula); 0 = homeowner keeps it
  life: number; // years
};

export function defaults(e: Economics): Assumptions {
  return { price: e.compute_price, occupancy: null, heatShare: 1, life: e.hardware.life_y };
}

export function hardware(e: Economics, n: number, life = e.hardware.life_y) {
  const hw = e.hardware;
  const installed = hw.installed_house_chf + hw.installed_server_chf * n;
  const maint = hw.maint_house_chf_yr + hw.maint_server_chf_yr * n;
  const cards = hw.cards_server_chf_yr * n;
  const insurance = hw.insurance_share_yr * installed;
  const uplink = hw.uplink_house_chf_yr;
  const depreciation = installed / life;
  const fixed = maint + cards + insurance + uplink;
  return { installed, depreciation, maint, cards, insurance, uplink, fixed, year: depreciation + fixed };
}

export function siteMoney(f: Fleet, s: Site, a: Assumptions) {
  const e = f.meta.economics;
  const simSold = s.year.run_server_h;
  const k = a.occupancy === null || !simSold ? 1 : Math.min(1, (a.occupancy * s.year.permit_server_h) / simSold);
  const sold = simSold * k;
  const electricity = sold * f.meta.constants.server_kw * e.electricity_chf_kwh;
  const heat = s.year.served_kwh * k * (e.electricity_chf_kwh / e.heat_pump_cop) * a.heatShare;
  const hw = hardware(e, s.servers, a.life);
  const income = sold * a.price;
  const cost = electricity - heat + hw.year;
  return {
    sold,
    electricity,
    heat,
    hw,
    income,
    cost,
    margin: income - cost,
    breakeven: sold ? (electricity - heat) / sold : NaN,
    priceNeeded: sold ? cost / sold : NaN,
    payback: income - (electricity - heat) - hw.fixed > 0 ? hw.installed / (income - (electricity - heat) - hw.fixed) : Infinity,
  };
}

export type SiteMoney = ReturnType<typeof siteMoney>;

export function fleetMoney(f: Fleet, a: Assumptions) {
  const rows = f.sites.map((s) => siteMoney(f, s, a));
  const sum = (g: (r: SiteMoney) => number) => rows.reduce((x, r) => x + g(r), 0);
  const sold = sum((r) => r.sold);
  const t = {
    sold,
    electricity: sum((r) => r.electricity),
    heat: sum((r) => r.heat),
    installed: sum((r) => r.hw.installed),
    depreciation: sum((r) => r.hw.depreciation),
    maint: sum((r) => r.hw.maint),
    cards: sum((r) => r.hw.cards),
    insurance: sum((r) => r.hw.insurance),
    uplink: sum((r) => r.hw.uplink),
    fixed: sum((r) => r.hw.fixed),
    income: sum((r) => r.income),
    cost: sum((r) => r.cost),
    margin: sum((r) => r.margin),
  };
  return {
    rows,
    ...t,
    breakeven: (t.electricity - t.heat) / sold,
    priceNeeded: t.cost / sold,
    payback: t.income - (t.electricity - t.heat) - t.fixed > 0 ? t.installed / (t.income - (t.electricity - t.heat) - t.fixed) : Infinity,
  };
}

/** Signed number with a real minus sign, same grouping as nf(). */
export const chf = (v: number, digits = 0) => `${v < 0 ? "−" : ""}${nf(Math.abs(v), digits)}`;

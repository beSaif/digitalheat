/*
 * DigitalHeat pilot estimator: calculation engine.
 *
 * Pure functions, no DOM. The same file runs in the browser (rechner/app.js) and in Node
 * (rechner/tests/validate.mjs), so the numbers on the page are the numbers that are tested.
 *
 * Pipeline
 *   1. weather   hourly temperature of a supported weather point (2025, 8,760 h), optional
 *                height correction to the house's terrain height
 *   2. demand    space heating  = UA × max(0, 20 °C − T) in every hour of a heating day
 *                                (heating day: mean of the file day's 24 hours < 12 °C)  [case formula]
 *                hot water      = residents × 3 kWh/day, flat over 24 h                    [case: 12 kWh/day for 4]
 *                UA [kW/K] comes from heated area × specific heat demand of the building class,
 *                or from the annual bill (calibration), or from the case house (10 kW at −5.6 °C).
 *   3. dispatch  every hour: recoverable heat → current demand → tank (charge) → tank (discharge)
 *                → existing heater for the rest. Surplus beyond a full tank is dumped and counted.
 *   4. sizing    smallest tested fleet (1–20 servers) whose annual coverage reaches the target
 *   5. money     server electricity, operator break-even, household savings (only with inputs)
 *   6. CO₂       only with baseline system, emission factors and an electricity-accounting rule
 */

// ---------------------------------------------------------------- constants (all shown on the page)
export const CASE = Object.freeze({
  serverKw: 1.0, // electrical draw per active server                       [case]
  recoveredKw: 0.8, // recoverable heat per active server (80 %)          [case]
  tankKwh: 35, // usable buffer, 1,000 l × 30 K, no losses                  [case]
  availability: 0.95, // share of each hour a server can run (jobs + hardware up)  [our assumption]
  indoorC: 20, // [case]
  heatingLimitC: 12, // heating day if daily mean < 12 °C                    [case]
  hwKwhPerPersonDay: 3, // 12 kWh/day for a household of four              [case]
  designPeakKw: 10, // case house: 10 kW at the coldest hour                [case]
  designSpreadK: 25.6, // 20 − (−5.6 °C)                                      [case]
  electricityRp: 33.25, // ElCom 2026, IWB Basel, H4, total                   [case + data/README.md]
  heatPumpCop: 2.5, // value of heat = electricity price ÷ 2.5                [case]
  computeChfPerServerH: 1.35, // scenario price, scripts/build_fleet_scenario.py COMPUTE_PRICE
  lapseKPer100m: 0.65, // standard atmosphere lapse rate                     [our assumption]
  heightCorrectionMinM: 100, // correct temperature only if heights differ by ≥ 100 m
  heightKmPer100m: 20, // nearest point: 100 m height difference counts like 20 km
  maxServers: 20, // tested fleets 1…20 (site: 5–20 kW per installed unit)
  hours: 8760,
});

/** Building classes: typical heating demand per m² heated area and year (Heizwärmebedarf),
 *  GEAK envelope classes as given by Kanton Solothurn, «Gebäude erneuern – Energieverbrauch halbieren».
 *  q = central value, lo/hi = band used for the range. G is open-ended; 200 is our cap. */
export const BUILDING_CLASSES = Object.freeze({
  neu: { label: "Neubau oder Minergie (ab ca. 2010)", geak: "A–B", q: 35, lo: 20, hi: 50 },
  ab2000: { label: "Ab 2000 gebaut oder umfassend saniert", geak: "C", q: 62, lo: 50, hi: 75 },
  ab1990: { label: "1990–1999 gebaut oder nachträglich gut gedämmt", geak: "D", q: 88, lo: 75, hi: 100 },
  teil: { label: "Teilweise saniert (z. B. neue Fenster, Dach gedämmt)", geak: "E", q: 112, lo: 100, hi: 125 },
  wenig: { label: "1970–1989, kaum gedämmt", geak: "F", q: 138, lo: 125, hi: 150 },
  alt: { label: "Vor 1970, unsaniert", geak: "G", q: 175, lo: 150, hi: 200 },
  unbekannt: { label: "Weiss ich nicht", geak: "–", q: 110, lo: 50, hi: 170 },
});

/** Existing heating systems. ef = kg CO₂e per kWh of purchased final energy, KBOB/ecobau list 2022
 *  V9.0 (data/raw/kbob/); eff = useful heat per kWh purchased (seasonal efficiency or JAZ), our
 *  assumption except the heat-pump JAZ, which follow the KBOB «Altbau» datasets. */
export const HEATING_SYSTEMS = Object.freeze({
  unbekannt: { label: "Weiss ich nicht", ef: null, eff: null, unit: "kWh" },
  oel: { label: "Ölheizung", ef: 0.324, kbob: "41.001 Heizöl EL", eff: 0.85, unit: "kWh Heizöl" },
  gas: { label: "Gasheizung", ef: 0.23, kbob: "41.002 Erdgas", eff: 0.9, unit: "kWh Gas" },
  wp_luft: { label: "Wärmepumpe Luft/Wasser", ef: 0.125, kbob: "45.020 Strom CH-Verbrauchermix", eff: 2.7, unit: "kWh Strom", jaz: true },
  wp_sole: { label: "Wärmepumpe Erdsonde", ef: 0.125, kbob: "45.020 Strom CH-Verbrauchermix", eff: 3.2, unit: "kWh Strom", jaz: true },
  elektro: { label: "Elektroheizung (direkt oder Speicher)", ef: 0.125, kbob: "45.020 Strom CH-Verbrauchermix", eff: 1.0, unit: "kWh Strom" },
  holz: { label: "Pellets oder Holz", ef: 0.0277, kbob: "41.008 Pellets", eff: 0.85, unit: "kWh Pellets" },
  fernwaerme: { label: "Fernwärme", ef: 0.0658, kbob: "42.016 Fernwärme Durchschnitt Netze CH", eff: 1.0, unit: "kWh Wärme" },
});
export const GRID_EF = 0.125; // kg CO₂e/kWh, KBOB 45.020 CH-Verbrauchermix
export const OIL_KWH_PER_L = 10; // 1 l Heizöl ≈ 10 kWh (same brochure: 4–5 l/m²a ≈ 40–50 kWh/m²a)

const DAYS = 365;
const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
/** month (0–11) of every hour; the weather files start 2025-01-01T00:00 and have 24 rows per day */
export const HOUR_MONTH = (() => {
  const m = new Uint8Array(8760);
  let h = 0;
  MONTH_DAYS.forEach((d, i) => m.fill(i, h, (h += d * 24)));
  return m;
})();
export const WINTER_MONTHS = [0, 1, 2, 9, 10, 11]; // Jan–Mar, Oct–Dec  (case: heating Oct–Mar)
export const isWinter = (month) => month <= 2 || month >= 9;

// ---------------------------------------------------------------- 1. location & weather
export function kmBetween(lat1, lon1, lat2, lon2) {
  const r = Math.PI / 180;
  const a = Math.sin(((lat2 - lat1) * r) / 2) ** 2 + Math.cos(lat1 * r) * Math.cos(lat2 * r) * Math.sin(((lon2 - lon1) * r) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}

export function gridElevation(grid, lat, lon) {
  const r0 = Math.round((lat - grid.lat0) / grid.dlat);
  const c0 = Math.round((lon - grid.lon0) / grid.dlon);
  let best = null;
  for (const [dr, dc] of [[0, 0], [-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [-1, 1], [1, -1], [1, 1]]) {
    const r = r0 + dr, c = c0 + dc;
    if (r < 0 || c < 0 || r >= grid.nrow || c >= grid.ncol) continue;
    const v = grid.elev[r * grid.ncol + c];
    if (v != null && (best === null || dr * dr + dc * dc < best[0])) best = [dr * dr + dc * dc, v];
  }
  return best ? best[1] : null;
}

/** Nearest supported weather point. Distance counts height: 100 m ≙ 20 km (heightKmPer100m). */
export function nearestPoint(points, lat, lon, elev = null) {
  let best = null;
  for (const p of points) {
    const km = kmBetween(lat, lon, p.lat, p.lon);
    const dh = elev == null ? 0 : Math.abs(elev - p.elev);
    const score = Math.hypot(km, (dh / 100) * CASE.heightKmPer100m);
    if (!best || score < best.score) best = { point: p, km, dh: elev == null ? null : elev - p.elev, score };
  }
  return best;
}

/** Temperatures in °C for one location; corrects for height if the house is ≥ 100 m above/below. */
export function locationTemps(tenths, pointElev, houseElev) {
  const dh = houseElev == null ? 0 : houseElev - pointElev;
  const shift = Math.abs(dh) >= CASE.heightCorrectionMinM ? (-CASE.lapseKPer100m * dh) / 100 : 0;
  const t = new Float64Array(tenths.length);
  for (let i = 0; i < t.length; i++) t[i] = tenths[i] / 10 + shift;
  return { temps: t, shiftK: shift, dh };
}

// ---------------------------------------------------------------- 2. demand
/** Heating degree-hours per hour: max(0, 20 − T) on heating days, else 0. */
export function degreeHours(temps) {
  const dh = new Float64Array(temps.length);
  let heatingDays = 0, hgt = 0, sum = 0;
  for (let d = 0; d < temps.length / 24; d++) {
    let mean = 0;
    for (let h = 0; h < 24; h++) mean += temps[d * 24 + h];
    mean /= 24;
    if (mean < CASE.heatingLimitC) {
      heatingDays++;
      hgt += CASE.indoorC - mean;
      for (let h = 0; h < 24; h++) {
        const v = Math.max(0, CASE.indoorC - temps[d * 24 + h]);
        dh[d * 24 + h] = v;
        sum += v;
      }
    }
  }
  return { dh, heatingDays, hgt, sum, minT: Math.min(...temps) };
}

/** UA in kW/K from area and specific heat demand q [kWh/m²a] valid in the reference climate. */
export const uaFromArea = (areaM2, q, hgtRef) => (q * areaM2) / (24 * hgtRef);
export const UA_CASE = CASE.designPeakKw / CASE.designSpreadK; // 0.390625 kW/K

/**
 * Useful heat that a bill stands for, and the share that is space heating.
 * bill = { amount, unit: 'kWh'|'l', kind: 'purchased'|'useful', includesHotWater: 'ja'|'nein'|'unsicher' }
 * Returns { ok, spaceKwh, usefulKwh, note }.
 */
export function billToSpaceHeat(bill, system, hwKwhYear) {
  if (!bill || !(bill.amount > 0)) return { ok: false, reason: "none" };
  if (bill.unit === "l" && (system.key !== "oel" || bill.kind !== "purchased")) return { ok: false, reason: "litres-not-oil" };
  const kwh = bill.unit === "l" ? bill.amount * OIL_KWH_PER_L : bill.amount;
  let useful = kwh;
  if (bill.kind === "purchased") {
    if (!system.eff) return { ok: false, reason: "needs-system" };
    useful = kwh * system.eff;
  }
  const withHw = bill.includesHotWater !== "nein"; // 'unsicher' → assume yes (one boiler for both is common)
  const space = withHw ? useful - hwKwhYear : useful;
  if (space < 0.2 * useful) return { ok: false, reason: "below-hot-water", usefulKwh: useful };
  return { ok: true, usefulKwh: useful, spaceKwh: space, assumedHotWater: withHw };
}

/**
 * Building model → { ua, method, uncertainty:{lo,hi} as factors on UA }.
 * input: { reference, areaM2, classKey, bill, system, hwKwhYear, dhSum, hgtRef }
 */
export function buildingModel(input) {
  if (input.reference) return { ua: UA_CASE, uaLo: UA_CASE, uaHi: UA_CASE, method: "reference", basis: "Fallstudie: 10 kW bei −5.6 °C" };
  const cls = BUILDING_CLASSES[input.classKey] ?? BUILDING_CLASSES.unbekannt;
  const fromBill = billToSpaceHeat(input.bill, input.system, input.hwKwhYear);
  if (fromBill.ok) {
    const ua = fromBill.spaceKwh / input.dhSum;
    // ±10 % for metered useful heat (weather of the bill year differs from 2025), ±15 % if the
    // efficiency of the boiler is assumed; ±20 % more if it is unclear whether hot water is included
    let u = input.bill.kind === "useful" ? 0.1 : 0.15;
    if (input.bill.includesHotWater === "unsicher") u += 0.1;
    return { ua, uaLo: ua * (1 - u), uaHi: ua * (1 + u), method: "bill", bill: fromBill, uncertainty: u, cls };
  }
  const ua = uaFromArea(input.areaM2, cls.q, input.hgtRef);
  return {
    ua,
    uaLo: uaFromArea(input.areaM2, cls.lo, input.hgtRef),
    uaHi: uaFromArea(input.areaM2, cls.hi, input.hgtRef),
    method: input.classKey && input.classKey !== "unbekannt" ? "class" : "default",
    cls,
    billProblem: fromBill.reason !== "none" ? fromBill.reason : null,
  };
}

/** Hourly demand in kWh: { space, hw, total } (Float64Array of 8,760) */
export function demandProfile(dh, ua, hwKwhPerDay) {
  const n = dh.length;
  const space = new Float64Array(n), hw = new Float64Array(n), total = new Float64Array(n);
  const hwH = hwKwhPerDay / 24;
  for (let i = 0; i < n; i++) {
    space[i] = ua * dh[i];
    hw[i] = hwH;
    total[i] = space[i] + hwH;
  }
  return { space, hw, total };
}

// ---------------------------------------------------------------- 3. hourly dispatch
const emptyBucket = () => ({ hours: 0, demand: 0, space: 0, hw: 0, served: 0, direct: 0, discharge: 0, charge: 0, backup: 0, dumped: 0, recovered: 0, serverH: 0, elecKwh: 0, peakDemand: 0 });

/**
 * One year, hour by hour.
 * opts: { servers, serverKw, recoveredKw, tankKwh, availability, mode: 'heat'|'always', whole: false }
 *   heat   (default) servers run only as much as demand + free tank space can take: no heat dumped
 *   always servers run at full available capacity; surplus beyond a full tank is dumped
 *   whole  run whole servers only (the repo's analysis/baseline_sweep.py convention, used as a cross-check)
 */
export function simulate(demand, opts) {
  const o = { serverKw: CASE.serverKw, recoveredKw: CASE.recoveredKw, tankKwh: CASE.tankKwh, availability: CASE.availability, mode: "heat", whole: false, ...opts };
  const n = demand.total.length;
  const months = Array.from({ length: 12 }, emptyBucket);
  const C = o.tankKwh, q1 = o.recoveredKw;
  const capServers = o.servers * o.availability;
  let soc = 0, socMin = Infinity, socMax = -Infinity, balanceErr = 0, tankErr = 0;
  for (let i = 0; i < n; i++) {
    const D = demand.total[i];
    let k; // servers running this hour (average)
    if (o.mode === "always") k = o.whole ? Math.floor(capServers + 1e-9) : capServers;
    else {
      const want = (D + (C - soc)) / q1;
      k = o.whole ? Math.min(Math.floor(capServers + 1e-9), Math.floor(want + 1e-9)) : Math.min(capServers, want);
    }
    const Q = k * q1;
    const direct = Math.min(Q, D);
    const surplus = Q - direct;
    const charge = Math.min(surplus, C - soc);
    const dumped = surplus - charge > 1e-9 ? surplus - charge : 0; // float noise is not dumped heat
    const soc0 = soc;
    soc += charge;
    const rest = D - direct;
    const discharge = Math.min(soc, rest);
    soc -= discharge;
    const backup = rest - discharge;
    // invariants: demand closes, heat closes, tank closes, tank stays in [0, C]
    balanceErr = Math.max(balanceErr, Math.abs(direct + discharge + backup - D), Math.abs(direct + charge + dumped - Q));
    tankErr = Math.max(tankErr, Math.abs(soc - (soc0 + charge - discharge)));
    socMin = Math.min(socMin, soc);
    socMax = Math.max(socMax, soc);
    const b = months[HOUR_MONTH[i]];
    b.hours++;
    b.demand += D;
    b.space += demand.space[i];
    b.hw += demand.hw[i];
    b.direct += direct;
    b.discharge += discharge;
    b.served += direct + discharge;
    b.charge += charge;
    b.backup += backup;
    b.dumped += dumped;
    b.recovered += Q;
    b.serverH += k;
    b.elecKwh += k * o.serverKw;
    if (D > b.peakDemand) b.peakDemand = D;
  }
  const sum = (list) => {
    const s = emptyBucket();
    for (const m of list) for (const key in s) s[key] = key === "peakDemand" ? Math.max(s[key], m[key]) : s[key] + m[key];
    return finish(s);
  };
  const finish = (s) => ({ ...s, coverage: s.demand ? s.served / s.demand : 0, avgServers: s.hours ? s.serverH / s.hours : 0 });
  return {
    servers: o.servers,
    opts: o,
    months: months.map(finish),
    winter: sum(months.filter((_, i) => isWinter(i))),
    summer: sum(months.filter((_, i) => !isWinter(i))),
    year: sum(months),
    finalSoc: soc,
    checks: { socMin, socMax, tankKwh: C, balanceErr, tankErr },
  };
}

// ---------------------------------------------------------------- 4. sizing
/** Smallest tested fleet that reaches the annual coverage target; else the best achieved. */
export function sizeFleet(demand, target, opts = {}) {
  const runs = [];
  for (let n = 1; n <= (opts.maxServers ?? CASE.maxServers); n++) runs.push(simulate(demand, { ...opts, servers: n }));
  const hit = runs.find((r) => r.year.coverage >= target - 1e-12);
  const best = runs.reduce((a, b) => (b.year.coverage > a.year.coverage + 1e-9 ? b : a));
  return { target, reached: Boolean(hit), recommended: hit ?? best, best, runs };
}

/** The case's two sanity checks for a demand profile. */
export function operatingPoints(demand, recoveredKw = CASE.recoveredKw) {
  let peakSpace = 0;
  for (let i = 0; i < demand.space.length; i++) peakSpace = Math.max(peakSpace, demand.space[i]);
  const hwDay = demand.hw.reduce((a, b) => a + b, 0) / DAYS;
  return {
    peakSpaceKw: peakSpace,
    serversForPeak: Math.ceil(peakSpace / recoveredKw - 1e-9),
    serversForPeakExact: peakSpace / recoveredKw,
    hwKwhDay: hwDay,
    serversForHotWater: hwDay / 24 / recoveredKw,
  };
}

// ---------------------------------------------------------------- 5. money
/**
 * prices: { serverElectricityRp, computeChfPerServerH, heatPriceRp (proposed, may be null),
 *           householdTariffRp (may be null), system { key, eff } }
 */
export function economics(run, prices) {
  const y = run.year;
  const elecCost = (y.elecKwh * prices.serverElectricityRp) / 100;
  const heatPriceSet = prices.heatPriceRp != null && prices.heatPriceRp >= 0;
  // operator side: heat is credited at the proposed heat price; without one, at the case rule
  // (heat replaces a heat pump with COP 2.5 at the Basel benchmark price)
  const caseHeatRp = CASE.electricityRp / CASE.heatPumpCop;
  const heatCreditRp = heatPriceSet ? prices.heatPriceRp : caseHeatRp;
  const heatRevenue = (y.served * heatCreditRp) / 100;
  const computeRevenue = y.serverH * prices.computeChfPerServerH;
  const breakEven = y.serverH ? (elecCost - heatRevenue) / y.serverH : NaN;
  const operator = {
    elecCost, heatRevenue, heatCreditRp, heatCreditSource: heatPriceSet ? "proposed" : "case",
    computeRevenue, breakEven, margin: computeRevenue + heatRevenue - elecCost, serverH: y.serverH,
  };

  // household side: needs the current system (efficiency), its tariff and a proposed heat price
  const sys = prices.system;
  const missing = [];
  if (!sys || !sys.eff) missing.push("system");
  if (!(prices.householdTariffRp > 0)) missing.push("tariff");
  const currentRpPerUseful = missing.length ? null : prices.householdTariffRp / sys.eff;
  if (!heatPriceSet) missing.push("heatPrice");
  const household = missing.length
    ? { available: false, missing, currentRpPerUseful }
    : {
        available: true,
        currentRpPerUseful,
        currentCostOfServed: (y.served * currentRpPerUseful) / 100,
        newCostOfServed: (y.served * prices.heatPriceRp) / 100,
        savings: (y.served * (currentRpPerUseful - prices.heatPriceRp)) / 100,
      };
  return { operator, household };
}

// ---------------------------------------------------------------- 6. CO₂
/**
 * accounting: 'elsewhere'  the computing would have run in a data centre anyway; its electricity
 *                          belongs to the computing, the house only avoids its own heating emissions
 *             'additional' the computing exists because of the installation; its electricity is
 *                          charged to the house at the Swiss consumer mix
 */
export function co2(run, system, accounting) {
  const missing = [];
  if (!system || system.ef == null || !system.eff) missing.push("system");
  if (accounting !== "elsewhere" && accounting !== "additional") missing.push("accounting");
  if (missing.length) return { available: false, missing };
  const perUseful = system.ef / system.eff; // kg per kWh of useful heat today
  const avoided = run.year.served * perUseful;
  const serverEmissions = run.year.elecKwh * GRID_EF;
  const net = accounting === "elsewhere" ? avoided : avoided - serverEmissions;
  return { available: true, accounting, perUseful, avoided, serverEmissions, net, baselineTotal: run.year.demand * perUseful };
}

// ---------------------------------------------------------------- one call for the page
/**
 * Full estimate. `weather` = { tenths, point, houseElev } ; others as above.
 * Returns everything the page shows, plus a low/high range when the inputs rely on defaults.
 */
export function estimate(inp) {
  const loc = inp.reference ? locationTemps(inp.weather.tenths, 0, null) : locationTemps(inp.weather.tenths, inp.weather.point.elev, inp.weather.houseElev);
  const dd = degreeHours(loc.temps);
  const residents = inp.reference ? 4 : inp.residents;
  const hwDay = residents * CASE.hwKwhPerPersonDay;
  const system = inp.system?.key && HEATING_SYSTEMS[inp.system.key]?.eff ? { ...HEATING_SYSTEMS[inp.system.key], key: inp.system.key, eff: inp.system.eff ?? HEATING_SYSTEMS[inp.system.key].eff } : null;
  const building = buildingModel({
    reference: inp.reference, areaM2: inp.areaM2, classKey: inp.classKey, bill: inp.bill,
    system: system ?? { key: "unbekannt", eff: null }, hwKwhYear: hwDay * DAYS, dhSum: dd.sum, hgtRef: inp.hgtRef,
  });
  const demand = demandProfile(dd.dh, building.ua, hwDay);
  const simOpts = { ...inp.sim };
  const sizing = sizeFleet(demand, inp.target, simOpts);
  const run = inp.servers ? simulate(demand, { ...simOpts, servers: inp.servers }) : sizing.recommended;

  // range: same installation, demand at the low and high end of what the inputs allow
  const hwU = inp.reference ? 0 : 0.25;
  const lo = simulate(demandProfile(dd.dh, building.uaLo, hwDay * (1 - hwU)), { ...simOpts, servers: run.servers });
  const hi = simulate(demandProfile(dd.dh, building.uaHi, hwDay * (1 + hwU)), { ...simOpts, servers: run.servers });
  const covs = [lo.year.coverage, run.year.coverage, hi.year.coverage];

  return {
    loc, dd, residents, hwDay, building, demand, sizing, run, system,
    range: { lo: Math.min(...covs), hi: Math.max(...covs), demandLo: lo.year.demand, demandHi: hi.year.demand, loRun: lo, hiRun: hi },
    points: operatingPoints(demand, simOpts.recoveredKw ?? CASE.recoveredKw),
    money: economics(run, { ...inp.prices, system }),
    co2: co2(run, system, inp.accounting),
  };
}

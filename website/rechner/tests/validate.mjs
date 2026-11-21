/*
 * Validation of the pilot estimator engine (website/rechner/model.js).
 *
 *   node website/rechner/tests/validate.mjs
 *
 * Exits non-zero if any check fails. Checks:
 *   A  Basel benchmark: the engine reproduces data/reference_house_2025_hourly.csv hour by hour
 *   B  Cross-check with analysis/baseline_sweep.py (independent Python code, whole servers)
 *   C  Tank capacity: state of charge stays within [0, tank] for every fleet, mode and tank size
 *   D  Hourly heat balance closes every hour and over the year
 *   E  Tariff slider: electricity cost and operator break-even respond linearly; 0.2261 CHF at 33.25 Rp
 *   F  Case sanity checks: 10 kW peak → 13 servers; 12 kWh/day hot water → 0.625 servers
 *   G  Sizing rule: smallest tested fleet reaching the target; best achieved when unreachable
 *   H  Bill calibration round trip, CO₂ / savings availability rules, location lookup
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import * as M from "../model.js";

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, "..", "..", "..");
const data = (p) => JSON.parse(readFileSync(join(here, "..", "data", p), "utf8"));

let failed = 0, passed = 0;
const check = (name, ok, detail = "") => {
  if (ok) passed++;
  else failed++;
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  — " + detail : ""}`);
};
const near = (a, b, tol) => Math.abs(a - b) <= tol;

const points = data("points.json");
const basel = data("weather/basel.json");
const ref = readFileSync(join(repo, "data", "reference_house_2025_hourly.csv"), "utf8").trim().split(/\r?\n/);
const head = ref[0].split(",");
const col = (name) => ref.slice(1).map((l) => Number(l.split(",")[head.indexOf(name)]));
const refTotal = col("total_heat_demand_kwh"), refSpace = col("space_heating_kwh"), refTemp = col("temperature_2m_c");

// ---------------------------------------------------------------- A
const temps = M.locationTemps(basel.t, 0, null).temps;
const dd = M.degreeHours(temps);
const caseDemand = M.demandProfile(dd.dh, M.UA_CASE, 12);
let maxDiff = 0, maxTempDiff = 0;
for (let i = 0; i < 8760; i++) {
  maxDiff = Math.max(maxDiff, Math.abs(caseDemand.total[i] - refTotal[i]));
  maxTempDiff = Math.max(maxTempDiff, Math.abs(temps[i] - refTemp[i]));
}
const sumArr = (a) => a.reduce((x, y) => x + y, 0);
check("A1 Basel weather = reference CSV temperatures", maxTempDiff < 1e-9, `max |ΔT| ${maxTempDiff}`);
check("A2 hourly demand = reference CSV (all 8,760 h)", maxDiff < 6e-5, `max |Δ| ${maxDiff.toExponential(2)} kWh (CSV rounded to 4 decimals)`);
check("A3 heating days = 206", dd.heatingDays === 206, String(dd.heatingDays));
check("A4 space heating = 26,850.5 kWh", near(sumArr(caseDemand.space), sumArr(refSpace), 0.01), sumArr(caseDemand.space).toFixed(2));
check("A5 total demand = 31,230.5 kWh", near(sumArr(caseDemand.total), 31230.55, 0.01), sumArr(caseDemand.total).toFixed(2));
check("A6 coldest hour −5.6 °C, UA = 10/25.6", dd.minT === -5.6 && M.UA_CASE === 0.390625);
// the page's "Basler Referenzhaus laden" path goes through estimate(); it must give the same demand
const refEst = M.estimate({ reference: true, weather: { tenths: basel.t }, target: 0.8, sim: { availability: 1 }, prices: { serverElectricityRp: 33.25, computeChfPerServerH: 1.35 }, hgtRef: points.hgt_ref });
check("A7 estimate(reference) demand = reference CSV total", near(refEst.run.year.demand, 31230.55, 0.01), refEst.run.year.demand.toFixed(2));

// ---------------------------------------------------------------- B
// printed by `python3 analysis/baseline_sweep.py` (policy follow, case assumptions)
const sweep = { 1: [19.5, 7629], 2: [32.7, 12782], 3: [45.5, 17769], 4: [58.0, 22654], 5: [69.9, 27271], 6: [79.6, 31067], 7: [87.1, 34000], 8: [92.9, 36281], 9: [96.9, 37836], 10: [99.3, 38749], 11: [100.0, 39044] };
const sweepAlways = { 1: [19.5, 903], 2: [32.8, 3786], 4: [58.0, 9903], 6: [79.6, 17191], 8: [92.9, 27037], 13: [100.0, 59839] };
let bOk = true, bMsg = [];
for (const [n, [cov, srvh]] of Object.entries(sweep)) {
  const r = M.simulate(caseDemand, { servers: Number(n), availability: 1, whole: true });
  const ok = near(r.year.coverage * 100, cov, 0.05) && Math.round(r.year.serverH) === srvh && r.year.dumped < 1e-9;
  if (!ok) { bOk = false; bMsg.push(`N=${n}: ${(r.year.coverage * 100).toFixed(2)} % ${r.year.serverH} h`); }
}
check("B1 follow policy = baseline_sweep.py, N=1…11 (coverage, server-hours, 0 dumped)", bOk, bMsg.join("; "));
bOk = true; bMsg = [];
for (const [n, [cov, dump]] of Object.entries(sweepAlways)) {
  const r = M.simulate(caseDemand, { servers: Number(n), availability: 1, whole: true, mode: "always" });
  const ok = near(r.year.coverage * 100, cov, 0.05) && Math.abs(r.year.dumped - dump) < 1;
  if (!ok) { bOk = false; bMsg.push(`N=${n}: ${(r.year.coverage * 100).toFixed(2)} % dumped ${r.year.dumped.toFixed(0)}`); }
}
check("B2 always-on policy = baseline_sweep.py (coverage, dumped kWh)", bOk, bMsg.join("; "));
const frac6 = M.simulate(caseDemand, { servers: 6, availability: 1 });
const whole6 = M.simulate(caseDemand, { servers: 6, availability: 1, whole: true });
check("B3 part-hour running (page default) ≥ whole servers, N=6", frac6.year.coverage >= whole6.year.coverage - 1e-12, `${(frac6.year.coverage * 100).toFixed(3)} % vs ${(whole6.year.coverage * 100).toFixed(3)} %`);

// ---------------------------------------------------------------- C + D
let cOk = true, dOk = true, worstBal = 0, worstTank = 0, cMsg = "";
for (const tank of [0, 10, 35, 200]) {
  for (const mode of ["heat", "always"]) {
    for (const whole of [false, true]) {
      for (let n = 1; n <= 20; n++) {
        for (const availability of [1, 0.95, 0.7]) {
          const r = M.simulate(caseDemand, { servers: n, tankKwh: tank, mode, whole, availability });
          const ck = r.checks;
          if (ck.socMin < -1e-9 || ck.socMax > tank + 1e-9) { cOk = false; cMsg = `tank ${tank} ${mode} N=${n}: [${ck.socMin}, ${ck.socMax}]`; }
          worstBal = Math.max(worstBal, ck.balanceErr);
          worstTank = Math.max(worstTank, ck.tankErr);
          const y = r.year;
          const closeDemand = Math.abs(y.served + y.backup - y.demand);
          const closeHeat = Math.abs(y.recovered - (y.served + y.dumped + r.finalSoc));
          if (closeDemand > 1e-6 || closeHeat > 1e-6) dOk = false;
          if (mode === "heat" && y.dumped > 1e-9) dOk = false;
          const seasons = Math.abs(r.winter.served + r.summer.served - y.served) + Math.abs(r.winter.serverH + r.summer.serverH - y.serverH);
          if (seasons > 1e-6) dOk = false;
          if (y.avgServers > n * availability + 1e-9) dOk = false;
        }
      }
    }
  }
}
check("C1 tank state of charge within [0, capacity], 960 runs (tank 0/10/35/200 kWh)", cOk, cMsg);
const r35 = M.simulate(caseDemand, { servers: 13, availability: 1 });
check("C2 35 kWh tank is used to its full capacity in a 13-server year", near(r35.checks.socMax, 35, 1e-9), `max ${r35.checks.socMax}`);
check("D1 every hour: direct + discharge + backup = demand; direct + charge + dumped = recovered", worstBal < 1e-9, `worst ${worstBal.toExponential(1)} kWh`);
check("D2 every hour: tank(t) = tank(t−1) + charge − discharge", worstTank < 1e-9, `worst ${worstTank.toExponential(1)} kWh`);
check("D3 year closes; heat-led runs dump 0 kWh; Winter + Sommer = Jahr; servers ≤ installed × availability", dOk);

// ---------------------------------------------------------------- E
const r6 = M.simulate(caseDemand, { servers: 6, availability: 1, whole: true });
const econ = (rp) => M.economics(r6, { serverElectricityRp: rp, computeChfPerServerH: 1.35, heatPriceRp: null });
const e33 = econ(33.25), e20 = econ(20), e50 = econ(50);
check("E1 break-even at 33.25 Rp./kWh = 0.2261 CHF per server-hour (repo figure)", near(e33.operator.breakEven, 0.2261, 0.00005), e33.operator.breakEven.toFixed(5));
check("E2 electricity cost = server-hours × 1 kW × price", near(e33.operator.elecCost, 31067 * 0.3325, 0.5) && near(e33.operator.elecCost, 10330, 0.5), `CHF ${e33.operator.elecCost.toFixed(1)} (sweep: 10,330)`);
const slope1 = (e50.operator.elecCost - e33.operator.elecCost) / (50 - 33.25), slope2 = (e33.operator.elecCost - e20.operator.elecCost) / (33.25 - 20);
check("E3 slider is linear: cost and break-even move by server-h/100 and 1/100 per Rp.", near(slope1, slope2, 1e-6) && near(slope1, r6.year.serverH / 100, 1e-6) && near(e50.operator.breakEven - e33.operator.breakEven, 0.1675, 1e-9));
check("E4 heat credit without a proposed price = 33.25 / 2.5 = 13.30 Rp./kWh (case rule), unaffected by slider", e20.operator.heatCreditRp === 13.3 && e50.operator.heatRevenue === e33.operator.heatRevenue);
check("E5 household savings hidden without tariff, system and proposed heat price", !e33.household.available && e33.household.missing.length === 3);
const hp = { key: "wp_luft", eff: 2.5 };
const eHh = M.economics(r6, { serverElectricityRp: 33.25, computeChfPerServerH: 1.35, heatPriceRp: 10, householdTariffRp: 33.25, system: hp });
check("E6 savings = served × (tariff/JAZ − heat price); at 13.30 Rp. saves 0", eHh.household.available && near(eHh.household.savings, r6.year.served * (13.3 - 10) / 100, 1e-9) &&
  near(M.economics(r6, { serverElectricityRp: 33.25, computeChfPerServerH: 1.35, heatPriceRp: 13.3, householdTariffRp: 33.25, system: hp }).household.savings, 0, 1e-9), `CHF ${eHh.household.savings.toFixed(0)}/yr at 10 Rp.`);

// ---------------------------------------------------------------- F
const op = M.operatingPoints(caseDemand);
check("F1 10 kW winter space-heating peak ÷ 0.8 kW = 12.5 → 13 running servers", near(op.peakSpaceKw, 10, 1e-9) && op.serversForPeak === 13, `${op.peakSpaceKw} kW → ${op.serversForPeakExact} → ${op.serversForPeak}`);
check("F2 12 kWh/day hot water = 0.625 continuously running servers", near(op.hwKwhDay, 12, 1e-9) && near(op.serversForHotWater, 0.625, 1e-12), `${op.serversForHotWater}`);

// ---------------------------------------------------------------- G
const s80 = M.sizeFleet(caseDemand, 0.8, { availability: 1, whole: true });
check("G1 target 80 %, case assumptions: 6 servers give 79.6 %, so 7 are recommended", s80.reached && s80.recommended.servers === 7, `${s80.recommended.servers} servers, ${(s80.recommended.year.coverage * 100).toFixed(1)} %`);
const sAll = M.sizeFleet(caseDemand, 0.9);
const smallest = sAll.runs.find((r) => r.year.coverage >= 0.9);
check("G2 recommendation is the smallest tested fleet at or above target (page defaults, 90 %)", sAll.recommended === smallest && sAll.runs[sAll.recommended.servers - 2].year.coverage < 0.9);
const sNo = M.sizeFleet(caseDemand, 0.99, { availability: 0.95, maxServers: 8 });
check("G3 unreachable target: reached = false, best achieved coverage and remaining backup reported", !sNo.reached && sNo.recommended === sNo.best && sNo.best.servers === 8 && sNo.best.year.backup > 0,
  `best ${(sNo.best.year.coverage * 100).toFixed(1)} %, backup ${sNo.best.year.backup.toFixed(0)} kWh`);
const covs = sAll.runs.map((r) => r.year.coverage);
check("G4 coverage never falls when a server is added", covs.every((c, i) => i === 0 || c >= covs[i - 1] - 1e-12));

// ---------------------------------------------------------------- H
const hgtRef = points.hgt_ref;
const plateau = points.points.filter((p) => p.region === "Plateau").map((p) => p.hgt).sort((a, b) => a - b);
check("H1 reference climate = median Plateau HGT 20/12", near(hgtRef, (plateau[12] + plateau[13]) / 2, 1e-9), `${hgtRef} Kd`);
const zurich = data("weather/zurich.json");
const zPoint = points.points.find((p) => p.id === "zurich");
const base = { weather: { tenths: zurich.t, point: zPoint, houseElev: zPoint.elev }, areaM2: 160, residents: 3, classKey: "teil", target: 0.8, sim: {}, prices: { serverElectricityRp: 33.25, computeChfPerServerH: 1.35 }, hgtRef };
const e1 = M.estimate(base);
const usefulInclHw = e1.run.year.demand;
const e2 = M.estimate({ ...base, classKey: "unbekannt", bill: { amount: usefulInclHw, unit: "kWh", kind: "useful", includesHotWater: "ja" } });
check("H2 bill round trip: useful heat incl. hot water → same UA as the class model", near(e2.building.ua, e1.building.ua, 1e-9) && e2.building.method === "bill", `${e1.building.ua.toFixed(5)} vs ${e2.building.ua.toFixed(5)} kW/K`);
const e3 = M.estimate({ ...base, system: { key: "oel" }, bill: { amount: (usefulInclHw - e1.hwDay * 365) / 0.85 / 10, unit: "l", kind: "purchased", includesHotWater: "nein" } });
check("H3 oil in litres, purchased, without hot water → same UA", near(e3.building.ua, e1.building.ua, 1e-9));
const eDef = M.estimate({ ...base, classKey: "unbekannt" });
const width = (e) => (e.range.demandHi - e.range.demandLo) / e.run.year.demand;
check("H4 demand range: bill < building class < defaults", width(e2) < width(e1) && width(e1) < width(eDef), `±${(width(e2) * 50).toFixed(0)} % / ±${(width(e1) * 50).toFixed(0)} % / ±${(width(eDef) * 50).toFixed(0)} %`);
const bad = M.estimate({ ...base, bill: { amount: 500, unit: "kWh", kind: "useful", includesHotWater: "ja" } });
check("H5 a bill below the hot-water estimate is rejected and the class model used", bad.building.method === "class" && bad.building.billProblem === "below-hot-water");
const noSys = M.estimate({ ...base, bill: { amount: 20000, unit: "kWh", kind: "purchased", includesHotWater: "ja" } });
check("H6 purchased energy without a heating system cannot be converted", noSys.building.billProblem === "needs-system");
check("H7 CO₂ unavailable without baseline system", !e1.co2.available && e1.co2.missing.includes("system"));
const eOil = M.estimate({ ...base, system: { key: "oel" }, accounting: "elsewhere" });
check("H8 CO₂ (oil, computing would run elsewhere) = served × 0.324 / 0.85", eOil.co2.available && near(eOil.co2.net, eOil.run.year.served * 0.324 / 0.85, 1e-6), `${eOil.co2.net.toFixed(0)} kg/yr`);
const eAdd = M.estimate({ ...base, system: { key: "oel" }, accounting: "additional" });
check("H9 CO₂ (additional computing) subtracts server electricity × 0.125", near(eAdd.co2.net, eOil.co2.net - eOil.run.year.elecKwh * 0.125, 1e-6));
const plz = data("plz.json");
const row4051 = plz.rows.find((r) => r[0] === 4051);
const near4051 = M.nearestPoint(points.points, row4051[4], row4051[5], row4051[6]);
check("H10 postcode 4051 Basel → weather point Basel, no height correction", near4051.point.id === "basel" && Math.abs(M.locationTemps(basel.t, near4051.point.elev, row4051[6]).shiftK) === 0, `${near4051.km.toFixed(1)} km, Δh ${near4051.dh} m`);
const row7500 = plz.rows.find((r) => r[0] === 7500);
const near7500 = M.nearestPoint(points.points, row7500[4], row7500[5], row7500[6]);
check("H11 postcode 7500 St. Moritz → St. Moritz weather point", near7500.point.id === "st_moritz", near7500.point.name);

// ---------------------------------------------------------------- report
const def = M.estimate({ reference: true, weather: { tenths: basel.t }, target: 0.8, sim: {}, prices: { serverElectricityRp: 33.25, computeChfPerServerH: 1.35 }, hgtRef });
const y = def.run.year;
console.log(`\nReference house, page defaults (availability 95 %, part-hour running, target 80 %):`);
console.log(`  ${def.run.servers} servers · coverage ${(y.coverage * 100).toFixed(1)} % · served ${y.served.toFixed(0)} kWh · backup ${y.backup.toFixed(0)} kWh · dumped ${y.dumped.toFixed(0)} kWh`);
console.log(`  winter Ø ${def.run.winter.avgServers.toFixed(2)} servers, ${(def.run.winter.coverage * 100).toFixed(1)} % · summer Ø ${def.run.summer.avgServers.toFixed(2)} servers, ${(def.run.summer.coverage * 100).toFixed(1)} %`);
console.log(`  electricity CHF ${def.money.operator.elecCost.toFixed(0)} · break-even ${def.money.operator.breakEven.toFixed(4)} CHF/server-h`);
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);

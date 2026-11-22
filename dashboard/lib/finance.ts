import type { Schedule } from "@/lib/schedule";

/*
 * Finance for one site: what it costs, what it earns, when it pays back.
 * Server-hours, electricity and heat come from the scheduler (/api/schedule); the costs below are ours.
 */

export const USD_CHF = 0.84; // data/prices_2026.json

/** Every cost we add on top of the scheduler, with where it comes from. */
export const COSTS = {
  server_chf: { v: 25000, label: "Server", unit: "CHF each", src: "2x AMD EPYC 9654, 192 cores, 1 kW: same chips as AWS c7a.48xlarge (data/prices_2026.json)" },
  install_site_chf: { v: 2500, label: "Installation per house", unit: "CHF once", src: "our estimate: heat exchanger to the tank, one electrical circuit, rack" },
  install_server_chf: { v: 100, label: "Installation per server", unit: "CHF once", src: "our estimate: mounting, cabling, water hookup" },
  maint_server_chf_y: { v: 120, label: "Maintenance per server", unit: "CHF / year", src: "our estimate: fans, disks, share of a service visit" },
  internet_site_chf_y: { v: 600, label: "Internet per house", unit: "CHF / year", src: "our estimate: Swiss fibre, about CHF 50 / month" },
  ops_server_chf_y: { v: 60, label: "Monitoring per server", unit: "CHF / year", src: "our estimate: remote monitoring and software" },
} as const;

/** One hour of a 1 kW, 192-core server in the cloud (CHF). */
export const CLOUD = [
  { id: "aws-od", name: "AWS on-demand", usd: 11.244, src: "c7a.48xlarge, Frankfurt (devzero.io, Nov 2026)" },
  { id: "azure-od", name: "Azure on-demand", usd: 7.2, src: "HB176rs v4, 176 cores, East US (vantage.sh, Nov 2026)" },
  { id: "aws-spot", name: "AWS spot", usd: 3.26, src: "c7a.48xlarge, Frankfurt (devzero.io, Nov 2026)" },
  { id: "azure-spot", name: "Azure spot", usd: 1.4, src: "HB176rs v4, East US, about 1.33–1.46 (vantage.sh, Nov 2026)" },
].map((c) => ({ ...c, chf: c.usd * USD_CHF }));

/** Our default price: AWS spot, because our compute pauses like spot capacity (data/prices_2026.json "sell_price"). */
export const DEFAULT_PRICE = Math.round(CLOUD.find((c) => c.id === "aws-spot")!.chf * 100) / 100;

export type HoursMode = "heat" | "always";

export function finance(s: Schedule, price: number, mode: HoursMode) {
  const site = s.sites[0];
  const x = s.series[0];
  const n = site.servers;
  const elec = s.constants.electricity_chf_kwh;
  const heatV = s.constants.heat_value_chf_kwh;
  const years = s.constants.hardware_years;

  // month by month, from the hourly schedule
  const months = Array.from({ length: 12 }, (_, m) => {
    const a = Date.UTC(s.year, m, 1) - Date.UTC(s.year, 0, 1);
    const b = Date.UTC(s.year, m + 1, 1) - Date.UTC(s.year, 0, 1);
    const [h0, h1] = [a / 3.6e6, b / 3.6e6];
    let run = 0;
    let served = 0;
    for (let t = h0; t < h1 && t < x.running.length; t++) {
      run += x.running[t];
      served += x.served[t];
    }
    if (mode === "always") run = n * (h1 - h0);
    return { run, served };
  });
  const runH = months.reduce((a, m) => a + m.run, 0);
  const servedKwh = months.reduce((a, m) => a + m.served, 0);

  const servers = n * s.constants.hardware_chf_per_server; // the scheduler's server price, CHF 25,000
  const install = COSTS.install_site_chf.v + n * COSTS.install_server_chf.v;
  const invest = servers + install;
  const maint = n * COSTS.maint_server_chf_y.v;
  const ops = COSTS.internet_site_chf_y.v + n * COSTS.ops_server_chf_y.v;
  const fixedM = (maint + ops) / 12;

  const monthly = months.map((m) => {
    const income = m.run * price;
    const heat = m.served * heatV;
    const power = m.run * elec; // 1 kW per running server
    return { income, heat, power, net: income + heat - power - fixedM };
  });
  const income = runH * price;
  const heat = servedKwh * heatV;
  const power = runH * elec;
  const cash = income + heat - power - maint - ops; // per year, before paying back the investment
  const profit = cash - invest / years;

  // cumulative cash over the server lifetime, starting in January
  const cum: number[] = [-invest];
  for (let i = 0; i < years * 12; i++) cum.push(cum[i] + monthly[i % 12].net);
  const k = cum.findIndex((v) => v >= 0);
  const paybackMonths = k < 0 ? null : k - 1 + -cum[k - 1] / (cum[k] - cum[k - 1]);

  const perH = (v: number) => (runH ? v / runH : 0);
  return {
    n,
    runH,
    utilisation: runH / (n * 8760),
    dumpedKwh: Math.max(0, runH * s.constants.heat_recovery - servedKwh),
    servedKwh,
    servers,
    install,
    invest,
    maint,
    ops,
    power,
    heat,
    income,
    cash,
    profit,
    cum,
    paybackMonths,
    years,
    // what one server-hour costs us, all in (hardware spread over its lifetime, heat credited)
    costPerH: perH(power + maint + ops + invest / years - heat),
    lifetimeProfit: cum[cum.length - 1],
  };
}
export type Fin = ReturnType<typeof finance>;

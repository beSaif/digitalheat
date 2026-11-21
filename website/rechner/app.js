/*
 * DigitalHeat pilot estimator: page logic. All numbers come from ./model.js.
 * No network calls except the static data files next to this script; nothing is sent anywhere.
 */
import * as M from "./model.js?v=20261121h";

const root = document.getElementById("rechner");

const DATA = new URL("./data/", import.meta.url);
const nf0 = new Intl.NumberFormat("de-CH", { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat("de-CH", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const nf2 = new Intl.NumberFormat("de-CH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nf3 = new Intl.NumberFormat("de-CH", { minimumFractionDigits: 1, maximumFractionDigits: 3 });
const nf4 = new Intl.NumberFormat("de-CH", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
const kwh = (v) => `${nf0.format(Math.round(v))} kWh`;
const chf = (v) => `CHF ${v < 0 ? "−" : ""}${nf0.format(Math.abs(Math.round(v)))}`;
const pct = (v) => `${nf0.format(Math.round(v * 100))} %`;
const rp = (v) => `${nf2.format(v)} Rp./kWh`;
const kg = (v) => `${nf0.format(Math.round(Math.abs(v) / 10) * 10)} kg CO₂e`;
const MONTHS = ["Jan", "Feb", "März", "Apr", "Mai", "Juni", "Juli", "Aug", "Sept", "Okt", "Nov", "Dez"];
const MONTHS_LONG = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"];
const servers = (v) => (v === 1 ? "1 Server" : `${nf0.format(v)} Server`);
const dativ = (v) => (v === 1 ? "1 Server" : `${nf0.format(v)} Servern`);
const avg = (v) => (v < 10 ? nf1.format(v) : nf0.format(v));

function init() {
  const $ = (sel, el = root) => el.querySelector(sel);
  const $$ = (sel, el = root) => [...el.querySelectorAll(sel)];
  const form = $("#est-form");
  const state = {
    points: null, grid: null, hgtRef: null, plz: null, weather: new Map(),
    season: "winter", reference: false, location: null, servers: null, est: null, calculated: false,
    assume: { serverKw: M.CASE.serverKw, recoveredKw: M.CASE.recoveredKw, tankKwh: M.CASE.tankKwh, availability: M.CASE.availability },
  };

  // ------------------------------------------------------------ static setup
  const classSel = $("[data-class-select]");
  for (const [k, c] of Object.entries(M.BUILDING_CLASSES)) classSel.add(new Option(k === "unbekannt" ? c.label : `${c.label}`, k, k === "unbekannt", k === "unbekannt"));
  classSel.value = "unbekannt";
  const sysSel = $("[data-system-select]");
  for (const [k, s] of Object.entries(M.HEATING_SYSTEMS)) sysSel.add(new Option(s.label, k));
  sysSel.value = "unbekannt";

  // insulated-pipe jackets (lighter core over the dark outline)
  for (const p of $$(".est-pipes .pipe:not(.pipe-halo)")) {
    const j = p.cloneNode();
    j.setAttribute("class", "pipe-jacket");
    j.setAttribute("stroke", "#e6e3da");
    j.setAttribute("stroke-width", "10");
    p.after(j);
  }
  buildRack(12);

  // ------------------------------------------------------------ data
  const loadJSON = (p) => fetch(new URL(p, DATA)).then((r) => {
    if (!r.ok) throw new Error(`${p}: ${r.status}`);
    return r.json();
  });
  const pointsReady = loadJSON("points.json").then((d) => {
    state.points = d.points;
    state.grid = d.grid;
    state.hgtRef = d.hgt_ref;
  });
  let plzPromise = null;
  const plzReady = () => (plzPromise ??= loadJSON("plz.json").then((d) => (state.plz = d.rows.map((r) => ({ plz: r[0], ort: r[1], gemeinde: r[2], kt: r[3], lat: r[4], lon: r[5], elev: r[6], key: norm(`${r[0]} ${r[1]} ${r[2]}`) })))));
  const weatherFor = async (id) => {
    if (!state.weather.has(id)) state.weather.set(id, loadJSON(`weather/${id}.json`).then((d) => d.t));
    return state.weather.get(id);
  };

  // illustration defaults: the reference house with page defaults
  pointsReady
    .then(() => weatherFor("basel"))
    .then((t) => {
      const e = M.estimate(referenceInputs(t));
      state.refEst = e;
      if (!state.est) updateFigure(e);
      selfCheck(t);
    })
    .catch((err) => setStatus(`Daten konnten nicht geladen werden (${err.message}). Bitte Seite über einen Webserver öffnen.`));

  // ------------------------------------------------------------ season toggle (shared)
  root.addEventListener("click", (ev) => {
    const b = ev.target.closest("[data-season-toggle] button[data-season]");
    if (!b) return;
    setSeason(b.dataset.season);
  });
  function setSeason(s) {
    state.season = s;
    for (const b of $$("[data-season-toggle] button")) b.setAttribute("aria-pressed", String(b.dataset.season === s));
    $("[data-figure]").dataset.season = s;
    updateFigure(state.est ?? state.refEst);
    highlightSeason();
  }

  // ------------------------------------------------------------ hotspots
  const setHotspot = (n) => {
    for (const el of $$("[data-hotspot]")) el.classList.toggle("is-active", el.dataset.hotspot === n);
    for (const el of $$("[data-hotspot-item]")) el.classList.toggle("is-active", el.dataset.hotspotItem === n);
  };
  root.addEventListener("click", (ev) => {
    const h = ev.target.closest("[data-hotspot]");
    if (!h) return;
    setHotspot(h.dataset.hotspot);
    const item = $(`[data-hotspot-item="${h.dataset.hotspot}"]`);
    if (item && item.getBoundingClientRect().top > window.innerHeight) item.scrollIntoView({ block: "nearest", behavior: "smooth" });
  });
  for (const li of $$("[data-hotspot-item]")) {
    li.addEventListener("mouseenter", () => setHotspot(li.dataset.hotspotItem));
    li.addEventListener("mouseleave", () => setHotspot(null));
  }

  // ------------------------------------------------------------ place search (combobox)
  const placeInput = $("#est-place");
  const list = $("#est-place-list");
  let options = [], active = -1;
  placeInput.addEventListener("focus", () => plzReady());
  placeInput.addEventListener("input", async () => {
    state.location = null;
    showError("place", "");
    await plzReady();
    const q = norm(placeInput.value.trim());
    options = q.length < 2 ? [] : searchPlaces(q);
    active = -1;
    renderOptions();
  });
  placeInput.addEventListener("keydown", (ev) => {
    if (list.hidden && ev.key !== "Enter") return;
    if (ev.key === "ArrowDown" || ev.key === "ArrowUp") {
      ev.preventDefault();
      active = (active + (ev.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
      renderOptions();
    } else if (ev.key === "Enter" && !list.hidden && options.length) {
      ev.preventDefault();
      choosePlace(options[Math.max(active, 0)]);
    } else if (ev.key === "Escape") closeList();
  });
  placeInput.addEventListener("blur", () => setTimeout(closeList, 150));
  list.addEventListener("mousedown", (ev) => {
    const li = ev.target.closest("li[data-i]");
    if (li) choosePlace(options[Number(li.dataset.i)]);
  });
  function searchPlaces(q) {
    const digits = /^\d+$/.test(q);
    const ort = [], gem = [], contains = [];
    for (const r of state.plz) {
      if (digits) { if (String(r.plz).startsWith(q)) ort.push(r); continue; }
      if (norm(r.ort).startsWith(q)) ort.push(r);
      else if (norm(r.gemeinde).startsWith(q)) gem.push(r);
      else if (r.key.includes(q)) contains.push(r);
    }
    return [...ort, ...gem, ...contains].slice(0, 8);
  }
  function renderOptions() {
    list.innerHTML = options.map((r, i) => `<li role="option" id="est-opt-${i}" data-i="${i}" aria-selected="${i === active}">${r.plz} ${esc(r.ort)}<small> · ${r.gemeinde !== r.ort ? "Gemeinde " + esc(r.gemeinde) + ", " : ""}${r.kt}</small></li>`).join("");
    list.hidden = options.length === 0;
    placeInput.setAttribute("aria-expanded", String(!list.hidden));
    if (active >= 0) placeInput.setAttribute("aria-activedescendant", `est-opt-${active}`);
    else placeInput.removeAttribute("aria-activedescendant");
  }
  function closeList() {
    list.hidden = true;
    placeInput.setAttribute("aria-expanded", "false");
  }
  function choosePlace(r) {
    placeInput.value = `${r.plz} ${r.ort}`;
    state.location = { lat: r.lat, lon: r.lon, elev: r.elev, label: `${r.plz} ${r.ort}`, source: "plz", kt: r.kt };
    closeList();
    showError("place", "");
    locationHint();
    if (state.calculated) recalc();
  }
  async function resolveTypedPlace() {
    if (state.location) return state.location;
    const q = norm(placeInput.value.trim());
    if (!q) return null;
    await plzReady();
    const exact = state.plz.find((r) => String(r.plz) === q) ?? state.plz.find((r) => norm(r.ort) === q || norm(r.gemeinde) === q) ?? searchPlaces(q)[0];
    if (exact) choosePlace(exact);
    return state.location;
  }

  // coordinates instead of a postcode
  const coordsBox = $("[data-coords]");
  $("[data-toggle-coords]").addEventListener("click", (ev) => {
    const on = coordsBox.hidden;
    coordsBox.hidden = !on;
    $(".est-field-place").dataset.placeMode = on ? "coords" : "search";
    ev.target.textContent = on ? "Stattdessen Postleitzahl oder Gemeinde eingeben" : "Stattdessen Koordinaten eingeben";
    placeInput.disabled = on;
    state.location = null;
    if (on) coordsBox.querySelector("input").focus();
  });
  coordsBox.addEventListener("input", () => {
    state.location = null;
    if (state.calculated) debounceRecalc();
  });
  function coordsLocation() {
    const lat = parseFloat(form.lat.value), lon = parseFloat(form.lon.value);
    if (!(lat >= 45.8 && lat <= 47.9 && lon >= 5.9 && lon <= 10.6)) return null;
    return { lat, lon, elev: M.gridElevation(state.grid, lat, lon), label: `${nf2.format(lat)} N, ${nf2.format(lon)} O`, source: "coords" };
  }
  function locationHint() {
    const hint = $("[data-place-hint]");
    const loc = state.location;
    if (!loc || !state.points) { hint.textContent = "Für das Wetter an Ihrem Standort."; return; }
    const n = M.nearestPoint(state.points, loc.lat, loc.lon, loc.elev);
    hint.textContent = n.km < 3 ? `Wetterdaten: ${n.point.name}.` : `Nächster unterstützter Wetterpunkt: ${n.point.name} (${nf0.format(n.km)} km).`;
  }

  // ------------------------------------------------------------ other inputs
  sysSel.addEventListener("change", () => { syncEff(); syncTariffHint(); });
  function syncEff() {
    const s = M.HEATING_SYSTEMS[sysSel.value];
    const f = $("[data-eff-field]");
    f.hidden = !s.eff;
    if (!s.eff) return;
    $("[data-eff-label]").textContent = s.jaz ? "Jahresarbeitszahl (JAZ)" : "Jahresnutzungsgrad";
    form.eff.placeholder = String(s.eff);
    if (!state.reference) form.eff.value = "";
    $("[data-eff-hint]").textContent = s.jaz
      ? `Wärme pro kWh Strom übers Jahr. Standard ${s.eff} (KBOB-Datensatz «Altbau»).`
      : `Nutzwärme pro kWh eingekaufter Energie. Standard ${s.eff} (Annahme).`;
  }
  function syncTariffHint() {
    const s = M.HEATING_SYSTEMS[sysSel.value];
    const hint = $("[data-tariff-hint]");
    $("[data-tariff-label]").textContent = s.eff ? `Ihr heutiger Tarif (Rp. pro ${s.unit})` : "Ihr heutiger Heiztarif (Rp./kWh)";
    hint.textContent = sysSel.value === "oel" ? "Heizöl: Preis in CHF pro 100 Liter ÷ 10 = Rp. pro kWh (1 Liter ≈ 10 kWh)."
      : s.eff ? "Preis pro kWh eingekaufter Energie, alles inklusive." : "Bitte zuerst das Heizsystem unter «Genauer berechnen» wählen.";
  }
  syncEff();
  syncTariffHint();

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    calculate(true);
  });
  form.addEventListener("change", (ev) => {
    if (ev.target === placeInput) return;
    if (state.calculated) debounceRecalc();
  });
  form.addEventListener("input", (ev) => {
    if (ev.target === placeInput || ev.target.type === "radio") return;
    if (state.calculated) debounceRecalc();
  });

  // reference house (demo)
  $("[data-load-reference]").addEventListener("click", () => setReference(true, true));
  $("[data-leave-reference]").addEventListener("click", () => setReference(false, false));
  function setReference(on, run) {
    state.reference = on;
    $("[data-reference-banner]").hidden = !on;
    $("[data-house-fields]").disabled = on;
    if (on) {
      placeInput.value = "4051 Basel (Referenzhaus)";
      form.area.value = "";
      form.area.placeholder = "Fallstudie";
      form.residents.value = "4";
      classSel.value = "unbekannt";
      sysSel.value = "wp_luft";
      syncEff();
      form.eff.value = "2.5";
      form.billAmount.value = "";
      $("[data-tariff]").value = "33.25";
      syncTariffHint();
      for (const k of ["place", "area", "residents"]) showError(k, "");
    } else {
      placeInput.value = "";
      form.area.placeholder = "z. B. 160";
      form.residents.value = "";
      form.eff.value = "";
      sysSel.value = "unbekannt";
      $("[data-tariff]").value = "";
      syncEff();
      syncTariffHint();
      state.location = null;
      placeInput.focus();
    }
    if (run) calculate(true);
  }

  // results controls
  $("[data-target]").addEventListener("change", () => { state.servers = null; recalc(); });
  root.addEventListener("click", (ev) => {
    const st = ev.target.closest("[data-servers-step]");
    if (st && state.est) {
      const cur = state.servers ?? state.est.run.servers;
      state.servers = Math.min(M.CASE.maxServers, Math.max(1, cur + Number(st.dataset.serversStep)));
      if (state.servers === state.est.sizing.recommended.servers) state.servers = null;
      recalc();
    }
    if (ev.target.closest("[data-servers-reset]")) { state.servers = null; recalc(); }
  });
  const priceRange = $("[data-price-range]"), priceInput = $("[data-price-input]");
  priceRange.addEventListener("input", () => { priceInput.value = priceRange.value; renderMoney(); });
  priceInput.addEventListener("input", () => {
    const v = parseFloat(priceInput.value);
    if (v >= 0) priceRange.value = String(Math.min(60, Math.max(5, v)));
    renderMoney();
  });
  $("[data-price-reset]").addEventListener("click", () => { priceInput.value = priceRange.value = "33.25"; renderMoney(); });
  for (const sel of ["[data-tariff]", "[data-heatprice]", "[data-compute]"]) $(sel).addEventListener("input", renderMoney);
  $("[data-mode]").addEventListener("change", recalc);
  $("[data-accounting]").addEventListener("change", recalc);
  for (const inp of $$("[data-assume]")) {
    const k = inp.dataset.assume;
    inp.value = k === "availability" ? state.assume[k] * 100 : state.assume[k];
    inp.addEventListener("input", () => {
      const v = parseFloat(inp.value);
      if (!(v >= Number(inp.min) && v <= Number(inp.max))) return;
      state.assume[k] = k === "availability" ? v / 100 : v;
      recalc();
    });
  }
  $("[data-assume-reset]").addEventListener("click", () => {
    state.assume = { serverKw: M.CASE.serverKw, recoveredKw: M.CASE.recoveredKw, tankKwh: M.CASE.tankKwh, availability: M.CASE.availability };
    for (const inp of $$("[data-assume]")) inp.value = inp.dataset.assume === "availability" ? state.assume.availability * 100 : state.assume[inp.dataset.assume];
    recalc();
  });

  // pilot enquiry
  $("[data-pilot-cta]").addEventListener("click", () => {
    const e = state.est;
    const msg = document.querySelector('#kontakt textarea[name="message"]');
    const box = document.querySelector('#kontakt input[value="waerme"]');
    if (box) box.checked = true;
    if (msg && e) {
      const where = state.reference ? "Basler Referenzhaus (Fallstudie)" : `${state.location?.label ?? ""}, ${form.area.value} m², ${form.residents.value} Personen`;
      msg.value = `Ich interessiere mich für einen DigitalHeat-Pilotstandort.\n\nUnverbindliche Ersteinschätzung aus dem Rechner: ${where}. ` +
        `Geschätzte Installation mit ${servers(e.run.servers)} deckt ${pct(e.run.year.coverage)} des jährlichen Wärmebedarfs (${kwh(e.run.year.demand)}).`;
    }
  });

  let resizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => state.est && renderChart(state.est.run), 150);
  });

  // ------------------------------------------------------------ calculation
  let timer = null;
  function debounceRecalc() { clearTimeout(timer); timer = setTimeout(recalc, 220); }
  function recalc() { if (state.calculated) calculate(false); }

  async function calculate(fromSubmit) {
    try {
      await pointsReady;
    } catch { return; }
    const inp = await readInputs(fromSubmit);
    if (!inp) return;
    const est = M.estimate(inp);
    state.est = est;
    state.inputs = inp;
    state.calculated = true;
    const res = $("[data-results]");
    res.hidden = false; // visible before rendering, so the chart can measure its width
    render(est, inp);
    if (fromSubmit) {
      setStatus("");
      res.focus({ preventScroll: true });
      res.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  async function readInputs(strict) {
    const sim = { ...state.assume, mode: $("[data-mode]").value };
    const common = {
      target: parseFloat($("[data-target]").value), sim, servers: state.servers, hgtRef: state.hgtRef,
      accounting: $("[data-accounting]").value, prices: prices(),
      system: sysSel.value !== "unbekannt" ? { key: sysSel.value, eff: parseFloat(form.eff.value) || undefined } : null,
    };
    if (state.reference) {
      const t = await weatherFor("basel");
      return { ...common, reference: true, weather: { tenths: t, point: state.points.find((p) => p.id === "basel") } };
    }
    let ok = true;
    let loc = null;
    if (!coordsBox.hidden) {
      loc = coordsLocation();
      if (!loc) { ok = false; showError("place", "Bitte Koordinaten in der Schweiz eingeben (z. B. 47.5596 und 7.5886)."); }
      else showError("place", "");
    } else {
      loc = await resolveTypedPlace();
      if (!loc) { ok = false; showError("place", placeInput.value ? "Diesen Ort finden wir nicht. Bitte Postleitzahl oder Gemeinde aus der Liste wählen." : "Bitte Postleitzahl oder Gemeinde eingeben."); }
    }
    const area = parseFloat(form.area.value);
    if (!(area >= 20 && area <= 2000)) { ok = false; showError("area", "Bitte eine Fläche zwischen 20 und 2'000 m² eingeben."); } else showError("area", "");
    const residents = parseInt(form.residents.value, 10);
    if (!(residents >= 1 && residents <= 20)) { ok = false; showError("residents", "Bitte 1 bis 20 Personen eingeben."); } else showError("residents", "");
    if (!ok) {
      if (strict) {
        setStatus("Bitte die markierten Felder ergänzen.");
        root.querySelector('[aria-invalid="true"]')?.focus();
      }
      return null;
    }
    state.location = loc;
    const near = M.nearestPoint(state.points, loc.lat, loc.lon, loc.elev);
    const t = await weatherFor(near.point.id);
    const amount = parseFloat(form.billAmount.value);
    const bill = amount > 0 ? { amount, unit: form.billUnit.value, kind: form.billKind.value, includesHotWater: form.billHw.value } : null;
    return { ...common, reference: false, weather: { tenths: t, point: near.point, houseElev: loc.elev }, near, areaM2: area, residents, classKey: classSel.value, bill };
  }

  function prices() {
    const num = (sel) => { const v = parseFloat($(sel).value); return Number.isFinite(v) ? v : null; };
    return {
      serverElectricityRp: num("[data-price-input]") ?? M.CASE.electricityRp,
      computeChfPerServerH: num("[data-compute]") ?? M.CASE.computeChfPerServerH,
      heatPriceRp: num("[data-heatprice]"),
      householdTariffRp: num("[data-tariff]"),
    };
  }

  function referenceInputs(t) {
    return { reference: true, weather: { tenths: t }, target: 0.8, sim: { ...state.assume }, hgtRef: state.hgtRef, prices: { serverElectricityRp: 33.25, computeChfPerServerH: 1.35 }, system: null };
  }

  // ------------------------------------------------------------ rendering
  function render(e, inp) {
    const y = e.run.year;
    const rec = e.sizing.recommended;
    const overridden = state.servers != null && state.servers !== rec.servers;
    $("[data-headline]").innerHTML = `Für dieses Haus deckt die geschätzte Installation <strong>${pct(y.coverage)}</strong> des jährlichen Wärmebedarfs.`;

    // range
    const lo = Math.round(e.range.lo * 100), hi = Math.round(e.range.hi * 100);
    const why = {
      reference: "Referenzhaus der Fallstudie: Gebäude und Warmwasser sind vorgegeben, darum keine Bandbreite.",
      bill: `Gebäudemodell aus Ihrer Rechnung kalibriert (±${nf0.format(e.building.uncertainty * 100)} %), Warmwasser aus der Personenzahl (±25 %).`,
      class: `Gebäude aus Fläche und Sanierungsstand geschätzt (GEAK-Klasse ${e.building.cls?.geak}: ${e.building.cls?.lo}–${e.building.cls?.hi} kWh/m²), Warmwasser aus der Personenzahl (±25 %). Mit einer Heizrechnung wird die Schätzung enger.`,
      default: `Ohne Angaben zum Gebäude rechnen wir mit einem typischen Haus (50–170 kWh/m²). Darum ist die Bandbreite gross. Unter «Genauer berechnen» wird sie enger.`,
    }[e.building.method];
    $("[data-range]").textContent = lo === hi ? why : `Bandbreite ${lo}–${hi} %. ${why}`;

    const metaParts = [`Wärmebedarf ${kwh(y.demand)} pro Jahr`];
    if (inp.reference) metaParts.unshift("Wetter: Basel 2025 (Referenzprofil der Fallstudie)");
    else {
      const n = inp.near;
      const shift = e.loc.shiftK;
      metaParts.unshift(n.km < 3 ? `Wetter: ${n.point.name} 2025` : `Wetter: nächster unterstützter Wetterpunkt ${n.point.name} (${nf0.format(n.km)} km entfernt, ${nf0.format(n.point.elev)} m ü. M.)` +
        (shift ? `, um ${nf1.format(Math.abs(shift))} °C ${shift < 0 ? "kühler" : "wärmer"} korrigiert für ${nf0.format(Math.abs(e.loc.dh))} m Höhenunterschied` : ""));
    }
    $("[data-meta]").textContent = metaParts.join(" · ") + ".";

    // sizing
    $("[data-servers]").textContent = nf0.format(e.run.servers);
    $("[data-servers-label]").textContent = overridden ? `Server getestet (Empfehlung: ${rec.servers})` : e.run.servers === 1 ? "Server empfohlen" : "Server empfohlen";
    const target = e.sizing.target;
    const rule = `Regel: die kleinste getestete Anlage (1 bis ${M.CASE.maxServers} Server à ${nf2.format(inp.sim.serverKw)} kW), die übers Jahr mindestens ${pct(target)} des Wärmebedarfs deckt.`;
    $("[data-sizing-rule]").textContent = e.sizing.reached
      ? `${rule} ${rec.servers - 1 >= 1 ? `Mit ${dativ(rec.servers - 1)} wären es ${pct(e.sizing.runs[rec.servers - 2].year.coverage)}.` : ""}`
      : rule;
    const warn = $("[data-target-warning]");
    warn.hidden = e.sizing.reached;
    if (!e.sizing.reached) warn.textContent = `Keine getestete Anlage erreicht ${pct(target)}. Am meisten schaffen ${servers(e.sizing.best.servers)} mit ${pct(e.sizing.best.year.coverage)}; ${kwh(e.sizing.best.year.backup)} pro Jahr kommen weiterhin von der bestehenden Heizung.`;
    $("[data-servers-reset]").hidden = !overridden;

    // table
    const n0 = (v) => nf0.format(Math.round(v));
    const rows = [
      ["Wärmebedarf", "kWh", (s) => n0(s.demand)],
      ["Nutzwärme aus Servern", "kWh", (s) => n0(s.served)],
      ["Anteil gedeckt", "", (s) => pct(s.coverage)],
      ["Wärme von der bestehenden Heizung", "kWh", (s) => n0(s.backup)],
      ["Ø laufende Server", "", (s) => avg(s.avgServers)],
      ["Weggekühlte Wärme", "kWh", (s) => n0(s.dumped)],
    ];
    const r = e.run;
    $("[data-season-table] tbody").innerHTML = rows.map(([label, unit, f]) => `<tr><th scope="row">${label}${unit ? ` <small>(${unit})</small>` : ""}</th><td data-col="winter">${f(r.winter)}</td><td data-col="summer">${f(r.summer)}</td><td data-col="year">${f(r.year)}</td></tr>`).join("");
    highlightSeason();
    renderChart(r);
    renderPoints(e, inp);
    renderMoney();
    renderCo2(e);
    renderHow(e, inp);
    updateFigure(e);
    const p = $("[data-visit-power]");
    p.textContent = ` (bei ${servers(e.run.servers)} rund ${nf0.format(e.run.servers * inp.sim.serverKw)} kW)`;
    syncBillWarning();
  }

  function highlightSeason() {
    for (const cell of $$("[data-season-table] [data-col]")) cell.classList.toggle("is-season", cell.dataset.col === state.season);
    for (const g of $$("[data-chart-plot] .month")) g.classList.toggle("is-dim", M.isWinter(Number(g.dataset.m)) !== (state.season === "winter"));
  }

  function renderPoints(e, inp) {
    const p = e.points, rec = inp.sim.recoveredKw;
    $("[data-points]").innerHTML = `
      <div><span class="k">${nf1.format(p.peakSpaceKw)} kW → ${p.serversForPeak}</span>
        <p><strong>Kälteste Winterstunde:</strong> ${nf1.format(p.peakSpaceKw)} kW Raumwärme ÷ ${nf2.format(rec)} kW pro Server = ${nf2.format(p.serversForPeakExact)}, also ${servers(p.serversForPeak)} laufend, um sie direkt zu decken.</p></div>
      <div><span class="k">${nf1.format(p.hwKwhDay)} kWh → ${nf3.format(p.serversForHotWater)}</span>
        <p><strong>Sommer, nur Warmwasser:</strong> ${nf1.format(p.hwKwhDay)} kWh pro Tag ÷ 24 h ÷ ${nf2.format(rec)} kW = ${nf3.format(p.serversForHotWater)} dauernd laufende Server.</p></div>
      <div class="est-points-wide"><p><strong>Eine Anlage für beides.</strong> Installiert sind ${servers(e.run.servers)}. Im Winter laufen im Mittel ${avg(e.run.winter.avgServers)}, im Sommer ${avg(e.run.summer.avgServers)}. Der Speicher glättet die Spitzen; was fehlt, liefert die bestehende Heizung.</p>
        <p>Zum Vergleich die Fallstudie: 10 kW ÷ 0.8 kW = 12.5 → 13 Server; 12 kWh/Tag = 0.625 Server.</p></div>`;
  }

  function renderMoney() {
    const e = state.est;
    const priceVal = parseFloat(priceInput.value);
    $("[data-price-reset]").hidden = Math.abs(priceVal - 33.25) < 1e-9;
    if (!e) return;
    const money = M.economics(e.run, { ...prices(), system: e.system });
    const o = money.operator;
    const y = e.run.year;
    $("[data-elec-cost]").innerHTML = `Stromkosten der Server: <strong>${chf(o.elecCost)}</strong> pro Jahr (${kwh(y.elecKwh)} Strom bei ${rp(prices().serverElectricityRp)}). Wer den Serverstrom bezahlt, regelt der Pilotvertrag; in dieser Rechnung trägt ihn der Betreiber.`;

    const h = money.household;
    const box = $("[data-savings]");
    if (h.available) {
      const saves = h.savings >= 0;
      box.innerHTML = `<p class="est-stat">${saves ? "Geschätzte Ersparnis" : "Geschätzte Mehrkosten"}: <strong>${chf(Math.abs(h.savings))}</strong> pro Jahr</p>
        <p>Die ${kwh(y.served)} Server-Wärme kosten Sie heute ${chf(h.currentCostOfServed)} (${rp(h.currentRpPerUseful)} Nutzwärme: Tarif ÷ ${nf2.format(e.system.eff)}). Mit Server-Wärme zu ${rp(prices().heatPriceRp)} wären es ${chf(h.newCostOfServed)}.</p>
        <p class="est-hint">Ohne Grundgebühren, Wartung und Investitionen. Die übrigen ${kwh(y.backup)} liefert weiterhin Ihre bestehende Heizung zum heutigen Preis.</p>`;
    } else if (h.currentRpPerUseful != null) {
      box.innerHTML = `<p>Ihre Wärme kostet heute <strong>${rp(h.currentRpPerUseful)}</strong> Nutzwärme (${rp(prices().householdTariffRp)} ÷ ${nf2.format(e.system.eff)}). Server-Wärme spart Ihnen Geld, wenn sie günstiger angeboten wird.</p>
        <p class="est-hint">Die Ersparnis erscheint, sobald ein Preis für Server-Wärme eingetragen ist.</p>`;
    } else {
      const need = [];
      if (h.missing.includes("system")) need.push("Ihr heutiges Heizsystem (unter «Genauer berechnen»)");
      if (h.missing.includes("tariff")) need.push("Ihr heutiger Tarif");
      if (h.missing.includes("heatPrice")) need.push("ein Preis für Server-Wärme");
      box.innerHTML = `<p><strong>Ersparnis noch nicht berechenbar.</strong> Dafür fehlen: ${need.join(", ")}.</p>`;
    }

    // operator panel
    const credit = o.heatCreditSource === "proposed" ? `zum angebotenen Preis von ${rp(o.heatCreditRp)}` : `nach Fallstudien-Regel: 33.25 ÷ 2.5 = ${rp(o.heatCreditRp)}`;
    $("[data-operator-out]").innerHTML = `
      <div><dt>Serverstunden pro Jahr</dt><dd>${nf0.format(o.serverH)}<small>Auslastung ${pct(o.serverH / (e.run.servers * 8760))}</small></dd></div>
      <div><dt>Rechenerlös</dt><dd>${chf(o.computeRevenue)}<small>${nf2.format(prices().computeChfPerServerH)} CHF × Serverstunden</small></dd></div>
      <div><dt>Wärmeerlös</dt><dd>${chf(o.heatRevenue)}<small>${kwh(y.served)} ${credit}</small></dd></div>
      <div><dt>Stromkosten</dt><dd>${chf(o.elecCost)}<small>${kwh(y.elecKwh)} × ${rp(prices().serverElectricityRp)}</small></dd></div>
      <div class="is-key"><dt>Break-even-Rechenpreis</dt><dd>${Number.isFinite(o.breakEven) ? nf4.format(o.breakEven) + " CHF" : "–"}<small>pro Serverstunde: (Strom − Wärmeerlös) ÷ Serverstunden</small></dd></div>
      <div><dt>Deckungsbeitrag vor Hardware</dt><dd>${chf(o.margin)}<small>Rechenerlös + Wärmeerlös − Strom</small></dd></div>`;
    $("[data-operator-note]").textContent = `Nicht enthalten: Hardware, Installation, Wartung, Versicherung und Internetanschluss. ${y.dumped > 0.5 ? `Im Dauerbetrieb werden ${kwh(y.dumped)} pro Jahr weggekühlt; dieser Strom bringt keinen Wärmeerlös.` : "Wärmegeführt wird keine Wärme weggekühlt."}`;
  }

  function renderCo2(e) {
    const c = e.co2;
    const out = $("[data-co2-out]");
    const acc = $("[data-accounting]").value;
    if (!c.available) {
      out.innerHTML = `<div class="est-co2-box is-missing"><p><strong>CO₂-Schätzung noch nicht verfügbar</strong></p>
        <p>Dafür brauchen wir Ihr heutiges Heizsystem (unter «Genauer berechnen»). Erst damit ist klar, wie viel CO₂ die Wärme verursacht, die die Server ersetzen. Die Emissionsfaktoren stammen aus der KBOB-Liste; die Annahme zur Rechenarbeit wählen Sie oben.</p></div>`;
      return;
    }
    const sys = e.system;
    const statement = acc === "elsewhere"
      ? "Annahme: Die Rechenarbeit wäre sonst in einem Rechenzentrum gelaufen. Ihr Strom gehört zur Rechenarbeit und wird dem Haus nicht angerechnet."
      : `Annahme: Die Rechenarbeit entsteht zusätzlich. Ihr Strom (${kwh(e.run.year.elecKwh)}) wird dem Haus mit dem Schweizer Verbrauchermix angerechnet: ${kg(c.serverEmissions)}.`;
    const head = c.net >= 0 ? `Vermeidet rund <strong>${kg(c.net)}</strong> pro Jahr` : `Verursacht netto rund <strong>${kg(c.net)}</strong> mehr pro Jahr`;
    out.innerHTML = `<div class="est-co2-box"><p class="est-stat">${head}</p>
      <p>${statement}</p>
      <p>Ersetzte Wärme: ${kwh(e.run.year.served)} aus ${sys.label} mit ${nf3.format(sys.ef)} kg CO₂e pro kWh ÷ ${nf2.format(sys.eff)} = ${nf3.format(c.perUseful)} kg pro kWh Nutzwärme (KBOB 2022, V9.0, ${sys.kbob}). Vermieden: ${kg(c.avoided)}. Serverstrom: ${M.GRID_EF} kg CO₂e pro kWh (KBOB 45.020, CH-Verbrauchermix).</p></div>`;
  }

  function renderHow(e, inp) {
    const b = e.building;
    const ua = b.ua;
    let building;
    if (b.method === "reference") building = `Fallstudie: 10 kW Heizleistung bei −5.6 °C, also ${nf1.format(ua * 1000)} W pro Kelvin Temperaturdifferenz.`;
    else if (b.method === "bill") {
      const bl = b.bill;
      building = `Aus Ihrer Rechnung: ${kwh(bl.usefulKwh)} Nutzwärme${inp.bill.kind === "purchased" ? ` (eingekaufte Energie × ${nf2.format(e.system.eff)})` : ""}${bl.assumedHotWater ? ` minus ${kwh(e.hwDay * 365)} Warmwasser` : ""} = ${kwh(bl.spaceKwh)} Raumwärme. Verteilt auf ${nf0.format(e.dd.sum)} Heizgradstunden am Standort: ${nf1.format(ua * 1000)} W/K. Annahme: Das Rechnungsjahr war ähnlich kalt wie 2025.`;
    } else {
      building = `${b.method === "class" ? `Sanierungsstand «${b.cls.label}» (GEAK-Klasse ${b.cls.geak})` : "Kein Sanierungsstand angegeben, typisches Haus"}: ${b.cls.q} kWh/m² Heizwärmebedarf × ${nf0.format(inp.areaM2)} m², gültig im Mittelland-Klima (HGT 20/12 = ${nf0.format(state.hgtRef)} Kd, Median der 26 Mittelland-Orte 2025) → ${nf1.format(ua * 1000)} W/K.`;
      if (b.billProblem) building += ` Ihre Rechnung wurde nicht verwendet: ${billProblemText(b.billProblem)}`;
    }
    const steps = [
      `<strong>Wetter.</strong> ${inp.reference ? "Basel 2025, stündlich (Open-Meteo), wie im Referenzprofil der Fallstudie." : `Stündliche Temperaturen 2025 (Open-Meteo) am Wetterpunkt ${inp.near.point.name}, ${nf0.format(inp.near.km)} km entfernt, ${nf0.format(inp.near.point.elev)} m ü. M.${e.loc.shiftK ? ` Ihr Standort liegt ${nf0.format(Math.abs(e.loc.dh))} m ${e.loc.dh > 0 ? "höher" : "tiefer"}: Temperaturen um ${nf1.format(Math.abs(e.loc.shiftK))} °C korrigiert (0.65 °C pro 100 m).` : ""} Der Wetterpunkt ist der nächste der 93 Orte, wobei 100 m Höhenunterschied wie 20 km zählen.`} Heiztage (Tagesmittel unter 12 °C): ${e.dd.heatingDays}.`,
      `<strong>Gebäude.</strong> ${building} Raumwärme pro Stunde = ${nf1.format(ua * 1000)} W/K × (20 °C − Aussentemperatur), nur an Heiztagen. Das ist die Formel der Fallstudie; beim Referenzhaus ergibt sie 26'851 kWh.`,
      `<strong>Warmwasser.</strong> ${e.residents} Personen × 3 kWh pro Tag = ${nf1.format(e.hwDay)} kWh pro Tag, gleichmässig über 24 Stunden (Fallstudie: 12 kWh für 4 Personen).`,
      `<strong>Stunde für Stunde, 8'760 Stunden.</strong> Jeder laufende Server braucht ${nf2.format(inp.sim.serverKw)} kW Strom und liefert ${nf2.format(inp.sim.recoveredKw)} kW nutzbare Wärme. Verfügbar ist die Rechenarbeit ${pct(inp.sim.availability)} der Zeit (Annahme: Wartung und Stunden ohne Aufträge). Die Wärme deckt zuerst den aktuellen Bedarf, ein Überschuss lädt den ${nf0.format(inp.sim.tankKwh)}-kWh-Speicher, der Speicher entlädt sich bei Bedarf, und den Rest liefert die bestehende Heizung. ${inp.sim.mode === "always" ? "Dauerbetrieb: Was nicht mehr in den vollen Speicher passt, wird weggekühlt und gezählt." : "Wärmegeführt: Die Server laufen nur so viel, wie Haus und Speicher aufnehmen; weggekühlte Wärme wird trotzdem gezählt (hier 0)."} Server dürfen Teilstunden laufen.`,
      `<strong>Dimensionierung.</strong> Getestet werden 1 bis ${M.CASE.maxServers} Server. Empfohlen wird die kleinste Anlage mit mindestens ${pct(e.sizing.target)} Jahresdeckung. Jahreswerte sind Summen der Stundenwerte.`,
      `<strong>Bandbreite.</strong> Dieselbe Anlage, gerechnet mit dem tiefsten und höchsten plausiblen Wärmebedarf: ${kwh(e.range.demandLo)} bis ${kwh(e.range.demandHi)} pro Jahr.`,
    ];
    $("[data-how-steps]").innerHTML = steps.map((s) => `<li>${s}</li>`).join("");
  }

  function billProblemText(code) {
    return {
      "needs-system": "Für eingekaufte Energie brauchen wir das Heizsystem, um sie in Nutzwärme umzurechnen.",
      "litres-not-oil": "Liter sind nur bei einer Ölheizung und eingekaufter Energie möglich.",
      "below-hot-water": "Der Wert ist kleiner als oder ähnlich wie der geschätzte Warmwasserbedarf. Bitte prüfen, ob Warmwasser enthalten ist oder ob es sich um einen Teilbetrag handelt.",
    }[code] ?? "";
  }

  // bill warning in the form
  function syncBillWarning() {
    const w = $("[data-bill-warning]");
    const e = state.est;
    const p = e?.building?.billProblem;
    w.hidden = !p;
    if (p) w.textContent = billProblemText(p);
  }

  // ------------------------------------------------------------ chart
  function renderChart(run) {
    const plotEl = $("[data-chart-plot]");
    const W = Math.max(300, Math.round(plotEl.clientWidth || 760)), H = W < 560 ? 240 : 300, m = { l: 52, r: 4, t: 26, b: 30 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const months = run.months;
    const max = Math.max(...months.map((x) => x.served + x.backup + x.dumped)) || 1;
    const step = niceStep(max / 4);
    const top = Math.ceil(max / step) * step;
    const yv = (v) => m.t + ih - (v / top) * ih;
    const band = iw / 12;
    const bw = Math.min(24, band * 0.5);
    const gap = 2;
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Wärme pro Monat: Server-Wärme und bestehende Heizung">`;
    // season bands
    s += `<rect class="band" x="${m.l}" y="${m.t - 20}" width="${band * 3}" height="${ih + 20}" opacity="0.6"/><rect class="band" x="${m.l + band * 9}" y="${m.t - 20}" width="${band * 3}" height="${ih + 20}" opacity="0.6"/>`;
    s += `<text class="band-label" x="${m.l + 6}" y="${m.t - 6}">Winter</text><text class="band-label" x="${m.l + band * 3 + 6}" y="${m.t - 6}">Sommer</text><text class="band-label" x="${m.l + band * 9 + 6}" y="${m.t - 6}">Winter</text>`;
    const short = W < 520;
    for (let v = 0; v <= top + 1e-9; v += step) {
      s += `<line class="grid" x1="${m.l}" x2="${W - m.r}" y1="${yv(v)}" y2="${yv(v)}"/><text class="axis-text" x="${m.l - 8}" y="${yv(v) + 4}" text-anchor="end">${v >= 10000 ? nf0.format(v / 1000) + "k" : nf0.format(v)}</text>`;
    }
    s += `<text class="axis-text" x="${m.l - 8}" y="${m.t - 12}" text-anchor="end">kWh</text>`;
    months.forEach((x, i) => {
      const cx = m.l + band * i + band / 2;
      const x0 = cx - bw / 2;
      const hS = (x.served / top) * ih, hB = (x.backup / top) * ih;
      const yS = m.t + ih - hS;
      s += `<g class="month" data-m="${i}">`;
      const topIsServer = hB < 0.5;
      if (hS > 0.5) s += roundedTop(x0, yS, bw, hS, topIsServer ? 4 : 0, "bar-server");
      if (hB >= 0.5) s += roundedTop(x0, yS - gap - hB, bw, hB, 4, "bar-backup");
      if (x.dumped > 0.5) { const hD = (x.dumped / top) * ih; s += `<rect class="bar-dump" x="${x0 + 0.75}" y="${yS - (hB >= 0.5 ? hB + gap : 0) - gap - hD}" width="${bw - 1.5}" height="${hD}" rx="3"/>`; }
      s += `<text class="axis-text" x="${cx}" y="${H - 12}" text-anchor="middle">${short ? MONTHS[i].slice(0, 1) : MONTHS[i]}</text>`;
      s += `<rect class="hit" x="${m.l + band * i}" y="${m.t}" width="${band}" height="${ih}" data-tip="${i}"/></g>`;
    });
    s += `<line x1="${m.l}" x2="${W - m.r}" y1="${m.t + ih}" y2="${m.t + ih}" stroke="#9aa1a5" stroke-width="1"/></svg>`;
    const plot = plotEl;
    plot.innerHTML = s;
    highlightSeason();

    const tip = $("[data-tooltip]");
    const show = (i, evx, evy) => {
      const x = months[i];
      tip.innerHTML = `<strong>${MONTHS_LONG[i]}</strong><i style="background:var(--est-server)"></i>Server: ${kwh(x.served)}<br><i style="background:var(--est-backup)"></i>Bestehende Heizung: ${kwh(x.backup)}<br>Gedeckt: ${pct(x.coverage)} · Ø ${avg(x.avgServers)} Server${x.dumped > 0.5 ? `<br>Weggekühlt: ${kwh(x.dumped)}` : ""}`;
      tip.hidden = false;
      const box = $("[data-chart]").getBoundingClientRect();
      const tw = tip.offsetWidth;
      tip.style.left = `${Math.min(Math.max(0, evx - box.left - tw / 2), box.width - tw)}px`;
      tip.style.top = `${Math.max(0, evy - box.top - tip.offsetHeight - 14)}px`;
    };
    for (const hit of plot.querySelectorAll("[data-tip]")) {
      hit.addEventListener("pointermove", (ev) => show(Number(hit.dataset.tip), ev.clientX, ev.clientY));
      hit.addEventListener("pointerleave", () => (tip.hidden = true));
    }
    $("[data-month-table]").innerHTML = `<thead><tr><th scope="col">Monat</th><th scope="col">Bedarf</th><th scope="col">Server-Wärme</th><th scope="col">Bestehende Heizung</th><th scope="col">Gedeckt</th><th scope="col">Ø Server</th></tr></thead><tbody>` +
      months.map((x, i) => `<tr><th scope="row">${MONTHS_LONG[i]}</th><td>${kwh(x.demand)}</td><td>${kwh(x.served)}</td><td>${kwh(x.backup)}</td><td>${pct(x.coverage)}</td><td>${avg(x.avgServers)}</td></tr>`).join("") + "</tbody>";
  }
  function roundedTop(x, y, w, h, r, cls) {
    r = Math.min(r, h, w / 2);
    return `<path class="${cls}" d="M${x} ${y + h} V${y + r} Q${x} ${y} ${x + r} ${y} H${x + w - r} Q${x + w} ${y} ${x + w} ${y + r} V${y + h} Z"/>`;
  }

  // ------------------------------------------------------------ illustration
  function buildRack(slots) {
    const g = $("[data-rack-slots]");
    const ns = "http://www.w3.org/2000/svg";
    for (let i = 0; i < slots; i++) {
      const y = 316 + i * 27;
      const slot = document.createElementNS(ns, "g");
      slot.innerHTML = `<rect class="est-rack-slot" x="104" y="${y}" width="122" height="22" rx="1.5"/>
        <path d="M112 ${y + 7} h60 M112 ${y + 11} h60 M112 ${y + 15} h60" stroke="#3f464a" stroke-width="1.2"/>
        <circle class="est-rack-glow" cx="214" cy="${y + 11}" r="9"/>
        <circle class="est-rack-led" cx="214" cy="${y + 11}" r="3"/>
        <circle class="est-rack-led est-rack-led-b" cx="202" cy="${y + 11}" r="2"/>`;
      g.appendChild(slot);
    }
  }
  function updateFigure(e) {
    if (!e) return;
    const winter = state.season === "winter";
    const s = winter ? e.run.winter : e.run.summer;
    const installed = e.run.servers;
    const shown = Math.min(installed, 12);
    const running = Math.min(shown, Math.max(s.avgServers > 0.05 ? 1 : 0, Math.round((s.avgServers * shown) / installed)));
    $$("[data-rack-slots] > g").forEach((g, i) => {
      g.querySelector(".est-rack-slot").classList.toggle("is-blank", i >= shown);
      const on = i < running;
      g.querySelector(".est-rack-led").classList.toggle("is-on", on);
      g.querySelector(".est-rack-glow").classList.toggle("is-on", on);
      g.querySelector(".est-rack-led-b").style.display = i < shown ? "" : "none";
    });
    const disp = $("[data-heater-display]");
    disp.textContent = winter ? (s.backup > 1 ? "Spitze" : "bereit") : "aus";
    const who = e === state.refEst || state.reference ? "Basler Referenzhaus" : "Ihr Haus";
    $("[data-season-caption]").textContent = winter
      ? `Winter (${who}): Im Mittel laufen ${avg(s.avgServers)} von ${dativ(installed)}${installed > 12 ? " (Abbildung zeigt 12 Einschübe)" : ""}. Ihre Abwärme geht über den Wärmetauscher in den Speicher und von dort in Heizkreis und Warmwasser. Die bestehende Heizung liefert ${pct(1 - s.coverage)} des Winterbedarfs, vor allem in kalten Stunden.`
      : `Sommer (${who}): Nur Warmwasser wird gebraucht, der Heizkreis bleibt aus. Im Mittel laufen ${avg(s.avgServers)} von ${dativ(installed)}. Ist der Speicher voll, pausieren die Server, statt Wärme wegzukühlen.`;
  }

  // ------------------------------------------------------------ helpers
  function showError(name, msg) {
    const el = $(`[data-error="${name}"]`);
    const input = name === "place" ? (coordsBox.hidden ? placeInput : form.lat) : form[name];
    if (el) { el.textContent = msg; el.hidden = !msg; }
    if (input) input.setAttribute("aria-invalid", msg ? "true" : "false");
  }
  function setStatus(msg) { $("[data-form-status]").textContent = msg; }
  function selfCheck(t) {
    const dd = M.degreeHours(M.locationTemps(t, 0, null).temps);
    const d = M.demandProfile(dd.dh, M.UA_CASE, 12);
    const total = d.total.reduce((a, b) => a + b, 0);
    const ok = Math.abs(total - 31230.55) < 0.05 && dd.heatingDays === 206;
    $("[data-selfcheck]").textContent = ok
      ? `Selbsttest beim Laden bestanden: Das Basler Referenzprofil wird reproduziert (${nf1.format(total)} kWh, 206 Heiztage). Vollständige Prüfung: node website/rechner/tests/validate.mjs (Referenzprofil Stunde für Stunde, Speichergrenzen, Wärmebilanz, Strompreis-Regler).`
      : `Selbsttest fehlgeschlagen: Referenzprofil ergibt ${nf1.format(total)} kWh statt 31'230.5 kWh.`;
  }
}

function norm(s) {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[-'’.]/g, " ").replace(/\s+/g, " ").trim();
}
function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
}
function niceStep(raw) {
  const p = 10 ** Math.floor(Math.log10(raw));
  const f = raw / p;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p;
}

if (root) init();

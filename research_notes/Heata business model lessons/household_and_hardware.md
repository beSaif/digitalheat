# Heata (heata.co): household side and hardware

Research date: 2026-11-21. Company legal name: Bit Warmer Limited (trading as "heata"), Company No. 11110428, Wood Farm, Godalming, Surrey ([Feb 2022 product sheet PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)).

**Status as of Nov 2026:** Still trading, and the business model is unchanged (servers on home hot-water cylinders, compute sold to businesses). The latest news post is dated 9 Oct 2026: heata won "Pitch in Whitehall: Green Compute", a UK government competition with a pilot contract as the prize. That page still says "Our servers sit in people's homes, attached to their hot water cylinders" ([heata, 9 Oct 2026](https://www.heata.co/content-hub/heata-wins-pitch-in-whitehall-green-compute)). The company-facing side now pushes a Ray / ML workload beta ([heata, 4 Jul 2025](https://www.heata.co/content-hub/from-ray-workloads-to-hot-water-the-heata-model-in-action)). I found no sign that it has pivoted away from households or ceased trading. Signup on the household side is still framed as registering interest "for a future pilot or to join the heata network as it expands" ([hosts sign-up page](https://www.heata.co/hosts-sign-up)). That suggests there is no open, general consumer rollout yet.

Source note: many hardware figures come only from the company: a Feb 2022 product sheet, the current website, and CTO comments on The Register forum. They are marked by date below. Figures differ between dates, so treat older ones as possibly outdated.

---

## 1. Hardware: what the unit is and how it couples to the cylinder

### Takeaway
The heata unit is a refurbished dual-Xeon compute server, roughly 300–330 W electrical. It bolts onto a patented aluminium-style "thermal bridge" that is fixed to the outside of a **vented** copper hot-water cylinder after a patch of foam insulation is cut away. Heat conducts through the cylinder wall. There is no plumbing and no heat exchanger in the water, and the unit is wired into the immersion-heater circuit. Heat into the tank is about 180–220 W at full power, i.e. up to about 4.8 kWh/day. When the water is hot, the processors throttle and the unit reduces work. It does not dump the heat anywhere else.

### Cited Findings
**Server and compute**
- Refurbished Xeon CPUs, "56 cores in total" (Jan 2023) — [The Register, 12 Jan 2023](https://www.theregister.com/2023/01/12/heata_offers_free_hot_water/)
- The CTO, Chris Jordan, said on The Register forum (Jan 2023) that the units "put between 180W and 200W into the tank when at full power", from twin 120 W Xeon CPUs (so about 240 W of CPU TDP), and that 200 W × 24 h = 4.8 kWh — [The Register forum thread, Jan 2023](https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/)
- 2022 product sheet footnote: "Heata: 300W/hour (300W compute, including 200W harnessed from waste heat)". It compares this with "Typical Data Centre + domestic hot water: 680W/hour (300W compute + 180W air conditioning + 200W hot water)" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Current website (2026): "330W compute, including 220W harnessed from waste heat" (footnote, at 80% utilisation) — [heata unit page](https://www.heata.co/free-hot-water/heata-unit)
- Described as "a powerful compute server, similar to those found in a data centre … heata has re-configured the hardware" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- I found no GPU in any source. Workloads cited include video/3D rendering (F10 Studios, Media Cymru render hub), Jupyter and Ray ML jobs — [heata BBC post, Dec 2023](https://www.heata.co/content-hub/did-you-spot-us-on-bbc-news); [GtR: heata x Media Cymru](https://gtr.ukri.org/find-research-and-innovation/project/efe30f5a-6ee3-460f-914e-037581df593f); [heata Ray post, Jul 2025](https://www.heata.co/content-hub/from-ray-workloads-to-hot-water-the-heata-model-in-action)
- The company says the hardware lasts about 4 years before it is uneconomic: "being outdated / unprofitable to run (perhaps 4 years) tends to happen before failure, a swap to new hardware will take about 30 minutes" (2022) — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)

**Heat into tank (all company claims; converted)**
| Claim | Date | kWh/day | Average W | kWh/yr (×365) | Source |
|---|---|---|---|---|---|
| "Up to 4.8kWh / day", "80% of an average UK household's hot water energy consumption" | Feb 2022 → current site | 4.8 | 200 W | 1,752 | [PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf); [FAQ](https://www.heata.co/free-hot-water) |
| Savings assumption "heata unit supplying 4.25kWh of hot water per day" | current site | 4.25 | 177 W | 1,551 | [heata unit page](https://www.heata.co/free-hot-water/heata-unit) |
| "up to 4kWh of hot water per day" | Feb 2025 (BG trial) | 4.0 | 167 W | 1,460 | [heata/BG release](https://www.heata.co/content-hub/british-gas-partners-with-heata-to-launch-innovative-trial-to-reuse-waste-heat-from-data-processing-and-save-households-money) |
| "about 3.6kWh" at expected utilisation | Oct 2023 | 3.6 | 150 W | 1,314 | [tech.eu, 24 Oct 2023](https://tech.eu/2023/10/24/heata-is-transforming-the-uks-household-energy-costs-with-waste-heat-reuse/) |
| "We are contractually obliged to provide 2.5kWh per day" | Feb 2022 | 2.5 | 104 W | 913 | [PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf) |
| 180–200 W into tank at full power | Jan 2023 | 4.3–4.8 | 180–200 W | 1,577–1,752 | [Register forum](https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/) |
- The basis heata uses for an average UK household: 4.67 kWh/day of hot water energy (1,705 kWh/yr), which it rounds to 195–200 W average. This comes from a DECC 2008 hot-water study, cited in the [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Current FAQ: "If the heata unit ran all day it would deliver about 4.8kWh … In practice the utilisation level will be lower and sometimes the water will be at temperature so the heata unit won't be able to run. We think it could deliver up to 80% of an average household's hot water, with good compute utilisation." — [heata free-hot-water FAQ](https://www.heata.co/free-hot-water)
- Heat delivery is described as "a steady trickle throughout the day, rather than a burst of intense heat like a kettle" — [heata unit page](https://www.heata.co/free-hot-water/heata-unit)

**Coupling to the cylinder**
- "Our patented thermal bridge is fitted to vented domestic hot water cylinders and provides the attachment point for our powerful server … heat … is transferred through the cylinder wall into the water" — [heata unit page](https://www.heata.co/free-hot-water/heata-unit)
- Installation steps (current FAQ): "a larger version of how a standard tank thermostat is installed - we remove a patch of the foam insulation (taking it down to the metal). Then we attach our thermal bridge to that section, the heata unit is then connected to that … We will also re-insulate the area if the heata unit is removed." — [heata FAQ](https://www.heata.co/free-hot-water)
- 2022 sheet: "Insulation is cut away and thermal bridge is attached to the cylinder. Replaceable heata unit bolted to thermal bridge. Heata unit is wired in to the immersion heater circuit. No plumbing required." "Existing immersion heater is used for top-up / backup." Patent GB2576035 — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Model H-DHW-RF-V-450-4800, "For 450mm diameter vented cylinders". Cylinder checklist: vented; diameter about 425–450 mm; a clear 226 × 320 mm patch of foam "just above the bottom curve"; 110 mm clear space straight out from the copper. The unit is 401 mm tall, 281 mm wide and extends 110 mm from the copper surface — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- "Fits vented hot water cylinders, a version for unvented cylinders is in development" (current site, undated). I found no evidence that an unvented version has shipped — [heata unit page](https://www.heata.co/free-hot-water/heata-unit)
- Some airing cupboards are too tight: "in some cases it won't be possible to install the unit" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)

**When the tank is full or hot (overheat protection, 2022)**
- "4 levels of overheat protection: 1. All processors throttle their speed (and therefore power output) when they reach their max operating temp. 2. The machine will monitor the case and water temperature on the machine and reduce work accordingly. 3. … auto reset-able thermal switch … 4. … non auto reset-able thermal cut out … as those found in standard immersion heaters, so as to comply with EN60335-2-73" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Current FAQ: "sometimes the water will be at temperature so the heata unit won't be able to run" — [heata FAQ](https://www.heata.co/free-hot-water)

**Noise, connectivity, security (2022 unless noted)**
- Noise: "variable speed low noise air circulation fans, no louder than 30dB (a whisper) at max speed" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Broadband (2022): "No, the heata unit uses its own connection, which will either be its own dedicated fibre line, or connection via 4G / 5G" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf). **This conflicts with later sources.** In Jan 2023 The Register reported that hosts need an internet connection and that heata was in talks with "several fiber broadband providers" ([The Register](https://www.theregister.com/2023/01/12/heata_offers_free_hot_water/)). The current signup form asks for "your broadband speed" ([hosts sign-up](https://www.heata.co/hosts-sign-up)).
- Network isolation: "Heata units are on a private subnet, isolated from the host's network and all network traffic goes out through a VPN (AES-256 encrypted)" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Physical security: "chassis intruder alarms, and all peripherals are disabled and physically inaccessible … storage … LUKS / AES-256 fully encrypted". It works with SUSE's secure edge platform — [Meet the heata unit, 25 Feb 2022](https://www.heata.co/content-hub/meet-the-heata-unit)
- EMC: "passed EMC testing … won't affect the host's electronic equipment, including WiFi" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)

### Inferences
- Electrical input is about 300–330 W, but heat into the water is about 180–220 W. That implies roughly 60–70% of the electricity reaches the tank and the rest is lost to the airing cupboard, mostly via fans and case losses. This is my inference from the company's own "330W compute, including 220W harnessed" figure (220/330 = 67%) and "300W … including 200W" (67%). In winter the airing-cupboard loss still heats the home, so it is not wasted then.
- Because the unit throttles when the tank is at temperature, the heat it delivers is capped by household hot-water demand, about 4.7 kWh/day on average. In summer, or in low-use homes, utilisation and therefore compute revenue fall. This is the "tank-full" constraint raised on The Register.
- Since heat goes in through the wall near the bottom of the cylinder, the unit preheats the cold layer. Temperature is topped up by the existing boiler coil or immersion heater (similar to solar thermal, as heata itself says).

### Gaps
- I found no published water temperatures (°C) reached by the unit alone, and no maximum-temperature setpoint.
- There is no current (2025–2026) spec sheet. The CPU model, GPU (none found), weight and current noise figure are not public. The current site omits dimensions.
- I found no published thermal-efficiency measurement (share of electricity that ends up in the water), only company footnotes.
- It is unclear whether the unit now uses the household's broadband or its own connection; the sources conflict, as above.

---

## 2. Who pays for the electricity, and how

### Takeaway
Heata pays. The unit's consumption is metered, either by a meter built into the power supply (2022) or by an "accredited billing submeter with a readable screen" (current). Heata reads it remotely and credits the host's energy account or bank account. In 2022 the credit was promised at **10% above market rate**. The current site gives no premium.

### Cited Findings
- Current FAQ (2026): "heata pays for the electricity used by the heata unit. Depending on your supplier, we'll either directly credit your energy account, or your bank account. An accredited billing submeter with a readable screen is included as part of the installation, which we will read remotely to get the details for your credit amounts." — [heata FAQ](https://www.heata.co/free-hot-water)
- Feb 2022: "Heata pays for the electricity to run the device, not the host. The electricity used by the unit is metered (the host can see the meter reading on the power supply unit) and the host is credited for the amount used, at 10% above the market rate." — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- "The unit's power supply has an integrated meter so we know exactly how much electricity it is using" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- CTO on The Register forum, Jan 2023: "We pay for all electricity used by the unit." — [Register forum](https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/)
- British Gas trial release, Feb 2025: "heata pays for the electricity the heata unit uses." — [heata/BG release, 5 Feb 2025](https://www.heata.co/content-hub/british-gas-partners-with-heata-to-launch-innovative-trial-to-reuse-waste-heat-from-data-processing-and-save-households-money)
- tech.eu, Oct 2023: usage is metered and the resident is credited — [tech.eu](https://tech.eu/2023/10/24/heata-is-transforming-the-uks-household-energy-costs-with-waste-heat-reuse/)
- Unverified: a 2023 hotukdeals user post says the electricity bill would be paid by "Innovate UK and Heata" during the trial. This is a user claim, not an official source (summarised via search; the thread page did not render) — [hotukdeals thread](https://www.hotukdeals.com/discussions/install-a-server-in-your-house-get-free-hot-water-4089302)

### Inferences
- At about 300–330 W continuous, the unit uses at most about 7.2–7.9 kWh/day (2,600–2,900 kWh/yr) at 100% utilisation. That is the volume heata would reimburse at the host's domestic tariff.
- The refund is "credit for kWh used", not a flat payment. So the host's net benefit is the boiler or immersion fuel saved, not a cash payment. The 10%-above-market premium (2022) would have been a small extra.

### Gaps
- No current statement on whether the credit is paid at the host's own tariff, a fixed rate, or with a premium, nor how often credits are paid.
- No information on hosts on prepayment meters (raised on The Register as a fuel-poverty issue).

---

## 3. What the household gets: savings, terms, eligibility, installation

### Takeaway
Free hot water as a base load, with electricity reimbursed and installation free in trials. Claimed bill savings have varied from £120 to £450/yr depending on date and fuel offset (the current site says "£150–350 a year"). Eligibility in practice: a **vented** hot-water cylinder (no combi boilers, no unvented cylinders yet), enough space in the airing cupboard, broadband, and a location in or near heata's Surrey/South-East area. Installers are heata's own engineers or electricians. British Gas tested and approved the procedure, but I found no evidence that British Gas engineers do the installs.

### Cited Findings
**Savings claims (by date; currency not converted)**
- 2020–21 Innovate UK study abstract: up to £300/yr — [GtR: Distributed Data Centres](https://gtr.ukri.org/find-research-and-innovation/project/83d2d3d3-0685-461c-af36-d9c756e2263e)
- Feb 2022: "Based on average household hot water yearly usage (water heated using electricity not gas), the host could save up to £200 / year." — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Oct 2023: up to £450/yr for an average household (this was during the 2022–23 energy price crisis) — [tech.eu](https://tech.eu/2023/10/24/heata-is-transforming-the-uks-household-energy-costs-with-waste-heat-reuse/)
- Feb 2025: "up to £340 per year when offsetting electrically heated hot water", and up to £120/yr when offsetting gas — [heata/BG release](https://www.heata.co/content-hub/british-gas-partners-with-heata-to-launch-innovative-trial-to-reuse-waste-heat-from-data-processing-and-save-households-money)
- Current site (2026): "Save £150–350 a year on your energy bill" — [heata free-hot-water](https://www.heata.co/free-hot-water)
- EPC claim (2022): "Expected 4-8 point EPC improvement", with heata "undertaking the SAP process 2022-2023" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf). Innovate UK funded "Harnessing heat from compute: SAP Accreditation" (Feb 2022–Sep 2023, £418,596) and "SAP Accreditation Stage 5b" (Mar–Jul 2024, £49,924) — [GtR SAP project](https://gtr.ukri.org/find-research-and-innovation/project/eb7681e0-9ddc-4561-a925-1bad02531fa6); [GtR search](https://gtr.ukri.org/search/project?term=%22Bit+Warmer%22)
- Carbon claim: "up to 1 tonne of CO₂ per unit per year" (2022, 2023) — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf); [The Register](https://www.theregister.com/2023/01/12/heata_offers_free_hot_water/)

**Terms, cost and installation**
- Trial units were free: "Because it's a government-backed trial, we're putting the units for free in people's houses" (CTO, Jan 2023). Hosts get "free hot water from it for a year" — [The Register](https://www.theregister.com/2023/01/12/heata_offers_free_hot_water/)
- 2022: an electrician installs in "under two hours", with no plumber needed — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf). Current site: "can be completed within a day". Photos show heata's own engineers ("Andrew", "Matt"), with a host quote: "My two installers were excellent." — [heata FAQ](https://www.heata.co/free-hot-water)
- British Gas: "We've tested the process with British Gas, and spoken to a leading cylinder manufacturer who confirmed that following the approved installation process won't invalidate your cylinder warranty" — [heata FAQ](https://www.heata.co/free-hot-water). The 2022 sheet says "Installation process tested and approved by British Gas" — [PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf). In the BG trial, the installer pictured is "Matt, the heata installer" — [heata/BG release](https://www.heata.co/content-hub/british-gas-partners-with-heata-to-launch-innovative-trial-to-reuse-waste-heat-from-data-processing-and-save-households-money)
- Maintenance (2022): "We schedule a yearly maintenance visit." Repairs: "The repairs team is notified automatically"; a unit swap takes "30 minutes or less" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)
- Fallback: "you'll still have hot water as it works alongside your current central heating system" — [heata FAQ](https://www.heata.co/free-hot-water)
- Hosts cannot use the compute: "the processing is used and paid for by companies" — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)

**Eligibility and target households**
- Vented cylinder required, with 425–450 mm diameter and clearances as in section 1 (2022). The unvented version is "in development" (current) — [PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf); [heata unit page](https://www.heata.co/free-hot-water/heata-unit)
- No combi boilers (a cylinder is needed) — per press summaries via search, e.g. [homebuilding.co.uk](https://homebuilding.co.uk/news/free-hot-water-from-your-wifi-the-smart-tech-revolution-that-could-help-homeowners-save) (not fetched directly; treat as secondary)
- The signup form asks for broadband speed, location and cylinder type. It lists no homeownership or tenure rules — [hosts sign-up](https://www.heata.co/hosts-sign-up)
- Social housing / landlord angle (2022): the product sheet is aimed at landlords. It defines the host as "the tenant", says "Free hot water for tenants", and mentions "New tenancies: EPC C by 2026". Joint applicant on the SAP project: Sero Life Limited, a housing-decarbonisation firm — [PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf); [GtR SAP project](https://gtr.ukri.org/find-research-and-innovation/project/eb7681e0-9ddc-4561-a925-1bad02531fa6). The current site still says "minimal disruption to tenants" — [heata FAQ](https://www.heata.co/free-hot-water)
- Fuel poverty: positioned as "helping households living in fuel poverty" and "free hot water to households that need it" (2022) — [PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)

### Inferences
- The savings range swings with fuel prices and with which fuel is offset: gas at about £120/yr versus electric immersion at about £340/yr. For gas-boiler homes, the realistic saving at 2025 prices is the lower end.
- Owners of the claimed 4.25 kWh/day (about 1,550 kWh/yr) offsetting electric immersion at about 22–25p/kWh would save roughly £340–390/yr, which fits heata's figure. Offsetting gas at about 6–7p/kWh and about 85–90% boiler efficiency would save roughly £110–130/yr. These are my calculations, not sourced, and the tariffs are approximate.
- The landlord/EPC framing (2022) appears to have faded from the current site, which targets individual "hosts". Whether SAP accreditation was obtained is not stated anywhere I found.

### Gaps
- No current contract terms for hosts: length, termination, liability, insurance, or what happens after the "one year".
- Whether installation is free outside trials is unknown; no consumer price has ever been published.
- I found no confirmation that heata obtained SAP/RdSAP accreditation or a measured EPC point gain.
- I found no explicit statements about homeownership versus renting, or social-housing deployments with named housing associations.

---

## 4. Trials: size, region, duration, results

### Takeaway
There are three phases. (1) Innovate UK-funded pilots in Surrey and the South East from about 2022–23: the plan was 100 units in 100 homes for 12 months, and The Register reported "about 100 units" for 3–6 months. (2) Continued hosting around Surrey and Gatwick, with BBC South East coverage in Dec 2023. (3) A 10-home, 3-month British Gas employee trial announced Feb 2025, running BG's own workloads. **No independent evaluation, measured-performance report, academic paper or published British Gas trial results were found.** The only measured output in public is one host's anecdote.

### Cited Findings
- Innovate UK "Distributed Data Centres (DDC)" study, Jan 2020–Mar 2021, £139,877 (with Sustainable Venture Development Partners). Its aim was a TRL8 "Hot Patch" unit for home trials — [GtR](https://gtr.ukri.org/find-research-and-innovation/project/83d2d3d3-0685-461c-af36-d9c756e2263e)
- Innovate UK "Harnessing heat from compute: SAP Accreditation", Collaborative R&D, 1 Feb 2022–30 Sep 2023, £418,596 total (Bit Warmer £391,022; Sero Life £27,574). The abstract plans to "build 100 alpha prototypes and run a 12-month pilot in 100 homes". GtR lists no outcomes or publications — [GtR](https://gtr.ukri.org/find-research-and-innovation/project/eb7681e0-9ddc-4561-a925-1bad02531fa6)
- Jan 2023: "about 100 units in individual homes, running for three to six months", in the South East of England — [The Register, 12 Jan 2023](https://www.theregister.com/2023/01/12/heata_offers_free_hot_water/)
- Oct 2023: "Trials have run in Surrey for over a year". The £1m seed round was led by Mark Boost (Civo), with Green Angel Syndicate and Innovate UK named — [tech.eu, 24 Oct 2023](https://tech.eu/2023/10/24/heata-is-transforming-the-uks-household-energy-costs-with-waste-heat-reuse/)
- Host anecdote (Irfan Walji, near Gatwick, BBC South East, Dec 2023): "We've generated over ten tonnes of hot water, which is about 90 days of average use of hot water and about 226 showers". Heata was "looking for more homes in Surrey" — [heata BBC post, 12 Dec 2023](https://www.heata.co/content-hub/did-you-spot-us-on-bbc-news). The hosts named on the site are in Gatwick, Ash Vale and Woking, all in Surrey or nearby — [heata FAQ](https://www.heata.co/free-hot-water)
- British Gas trial (announced 5 Feb 2025): "10 heata units will be installed in the homes of British Gas employees", a "three-month trial". BG's own data processing runs on the units. "The trial will provide feedback around performance and customer experience, as well as demonstrating the associated CO2 and energy cost savings." — [heata/BG release](https://www.heata.co/content-hub/british-gas-partners-with-heata-to-launch-innovative-trial-to-reuse-waste-heat-from-data-processing-and-save-households-money); [DCD](https://www.datacenterdynamics.com/en/news/british-gas-teams-up-with-heata-to-explore-using-cloud-computing-to-warm-homes/); [ITPro](https://www.itpro.com/infrastructure/data-centres/british-gas-launches-trial-scheme-to-reuse-waste-heat-from-data-processing-and-it-involves-installing-a-tiny-virtual-data-center-in-homes). (The Centrica copy of the release returned 403: [centrica.com](https://www.centrica.com/media-centre/news/2025/british-gas-partners-with-heata-on-trial-to-reuse-waste-heat-from-data-processing/))
- Origins: heata reportedly "began as an innovation project with British Gas" (per hotukdeals / Tom's Hardware summaries via search, not verified directly). British Gas is listed as a backer on heata's site — [heata FAQ](https://www.heata.co/free-hot-water)
- Other public funding: "heata x Media Cymru: Sustainable Render Hub", Mar 2024–Sep 2026, £156,518 (SiPF) — [GtR](https://gtr.ukri.org/find-research-and-innovation/project/efe30f5a-6ee3-460f-914e-037581df593f). A carbon comparison hackathon with Microsoft was held in Feb 2024 — [heata post](https://www.heata.co/content-hub/data-centre-carbon-hackathon-microsoft-azure-centralised-vs-heata-distributed)
- Carbon claim for the processing: "~40%" lower than a typical data centre (Feb 2022), later "~56 percent" (Oct 2023) — [Meet the heata unit](https://www.heata.co/content-hub/meet-the-heata-unit); [tech.eu](https://tech.eu/2023/10/24/heata-is-transforming-the-uks-household-energy-costs-with-waste-heat-reuse/)

### Inferences
- The host anecdote of "ten tonnes of hot water" ≈ 90 days of average use. Ten tonnes heated by about 40–45 K is roughly 470–520 kWh, i.e. about 5 kWh/day if delivered over 90 days. But the period over which it was delivered is not stated, so actual kWh/day cannot be derived. This is my calculation.
- The British Gas trial was small (10 employee homes, 3 months), so it is a proof of concept rather than a scale deployment. Its absence from later announcements suggests no scale-up had been made public by Nov 2026.
- The total installed base is unknown. The roughly 100-unit plan of 2022–23 is the only sizing figure, and the current site still recruits for a "future pilot".

### Gaps
- No published evaluation, final report, academic paper, Carbon Trust or Energy Saving Trust assessment, or Innovate UK outcome summary was found.
- I found no measured hot-water delivery (kWh/day across the fleet), utilisation, uptime, or satisfaction survey results.
- The British Gas trial outcomes are unpublished as of Nov 2026.
- Fleet size today is unknown.

---

## 5. Problems, criticism and risks

### Takeaway
There are no documented host complaints or reliability incidents in public sources. Criticism is mostly from tech forums (The Register, Jan 2023; Slashdot, Feb 2023). Commenters said the heat is small (about 180–200 W), electricity is a costly heat source, the tank fills up in summer, wall-conducted heat transfer through foam-insulated tanks is doubtful, dust and noise are concerns, hardware lifetime is short, truck-rolls cost money, network connectivity is weak, and data security is a risk. I found no Hacker News thread about Heata.

### Cited Findings (all from [The Register forum, Jan 2023](https://forums.theregister.com/forum/all/2023/01/12/heata_offers_free_hot_water/) unless noted)
- Small output: the CTO confirmed 180–200 W into the tank at full power, from twin 120 W Xeons.
- Electricity as heat: "electricity is generally considered to be the most expensive way to generate heat" (Charlie Clark). Others noted that the model may rely on cheap domestic versus commercial tariffs: "domestic electricity is cheaper due to government intervention" (Crypto Monad). The company still pays for the household's electricity at domestic rates.
- Tank full or seasonal: "Will the server's load be scaled down in the summer" (Korev). The need "to shut the server down when the water tank reaches its maximum temperature" (Crypto Monad). The CTO replied that it "only provide[s] a base load".
- Heat transfer doubt: "how much of that heat is going to make its way into the water?" (katrinab). The patent's insulation-cutting method "does not inspire confidence" (emfiliane).
- Legionella: cylinders should stay at 55 °C or above; the CTO said "we don't touch the heating already in place so no change the legionella risk".
- Noise and environment: "Rack mounted data centre equipment is not quiet" (AC). Lofts and cupboards are dusty and see temperature swings (Lee D). The company's own 2022 claim is ≤30 dB ([PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)).
- Lifetime and service cost: the units "are going to come to the end of their life" in a few years, and site visits erode the economics (Vikingforties). There are "no economies of scale" (John Brown). Rivals like Qarnot and district-heat reuse "make more sense".
- Security and reliability: "a glaring risk over the data security and server reliability" (Charlie Clark). Few workloads suit "a server with poor network connectivity" (Crypto Monad).
- Fuel poverty: "So the server will work until the prepayment meter cuts the electricity off?" (Dan 55).
- Slashdot discussion of the Tom's Hardware piece (Feb 2023) asked similar questions about who pays for electricity — [Slashdot](https://news.slashdot.org/story/23/02/16/0253250/heata-offers-uk-residents-free-hot-water-in-exchange-for-cooling-its-servers)
- TechRadar framed the BG trial as "free … but there's a catch" (2025; not fetched directly) — [TechRadar](https://techradar.com/pro/a-data-center-in-every-home-energy-company-wants-to-heat-your-water-for-almost-free-but-theres-a-catch)
- Company mitigations: four-level overheat protection, intruder alarms, encrypted storage, VPN with subnet isolation, automatic fault alerts, and an existing boiler or immersion heater as backup — [Feb 2022 PDF](https://uploads-ssl.webflow.com/6172c719d273286e95006270/6230cfe91838b1e5d763cab5_heata-compute%20powered%20water%20heater_Feb22.pdf)

### Inferences
- The main structural limits are (a) about 200 W of tank heat, capped by daily hot-water demand, so utilisation falls when the tank is satisfied, and (b) per-home service costs for about 300 W of compute that becomes obsolete in about 4 years. Neither has been addressed with published data.
- Vented cylinders are declining (combi boilers and unvented systems dominate new installs), which limits the addressable market until an unvented version ships.

### Gaps
- I found no first-hand host complaints, Reddit threads, or reports of failures, outages or uptime.
- I found no Hacker News thread on Heata; searches returned only Slashdot and The Register.
- No security incidents or independent security audits were reported.
- The hotukdeals thread (which may contain host comments) did not render its comments.

*Firecrawl credits ran out midway through this research; the remaining sources were fetched with WebFetch and WebSearch.*

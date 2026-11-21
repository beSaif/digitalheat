# Comparable operators: compute-as-heat business models (comparators to Heata, for DigitalHeat)

Research date: 2026-11-21. Currencies are as reported; nothing has been converted. "Search snippet" means the claim came from a search-result summary because the page itself blocked fetching (HTTP 403). Treat those as lower confidence than claims from fetched pages.

Summary table (details and sources are in the sections below):

| Operator | Who pays electricity | Host terms for heat | Unit size / temp | Compute customers | Status (Nov 2026) |
|---|---|---|---|---|---|
| Qarnot (FR) | Qarnot for Q.rad/QH-1 in buildings; the buyer for the QC-1 crypto heater | Heat free to social-housing tenants and offices; later sold heat to networks | ~500 W heaters; QC-1 500-650 W; boilers of up to 12 servers; 100 kW pilot; 500 kW-MW targets | Banks (BNP Paribas, Société Générale), Illumination (3D), research | Redressement judiciaire 19 May 2026; bought by Scaleway, announced 10 Jul 2026 |
| Deep Green (UK) | Deep Green (pays directly or refunds the host; reports differ) | Heat free, plus free install and maintenance | Exmouth pilot "12 four-CPU cards" or "50 kW" (conflicting); now 5-24 MW sites | Cloud and colocation tenants, e.g. a post-production firm, AI | Active; £200M Octopus commitment (Jan 2024); Lansing 24 MW plan withdrawn Apr 2026 |
| Cloud&Heat / AoTerra (DE) | Operator, for 15 years | Owner paid ~€12,000 up front for 15 years of heat | Server cabinets in homes and basements | Cloud storage and VMs | Residential model shut down; realignment 2022/23; now Kubernetes and on-prem |
| Nerdalize (NL) | Nerdalize (Eneco in the 2015 trial) | Free heat; €400 entry fee in the 2017 model | Radiator/boiler units at 45-55 °C | Businesses (cheap compute and storage) | Bankrupt 27 Dec 2018; a restart was reported |
| Leafcloud (NL) | Leafcloud (metered) | Free baseload heat; no host payment stated | 20-120 kW; 45-65 °C; 10-50 m² | Public cloud and GPU users | Active; seed from The Sharing Group (2025); 5x AI capacity from Q1 2026 |

---

## 1. Who pays the electricity, and what does the host get (free heat, pays for heat, or gets paid)?

### Takeaway
Every operator that places servers in someone else's building pays the server electricity. The deals differ in what the host gives in return: (a) nothing, and receives heat free (Qarnot housing, Deep Green, Leafcloud, Nerdalize 2015, Heata); (b) an up-front payment for long-term heat (Cloud&Heat/AoTerra ~€12,000 for 15 years; Nerdalize 2017 €400 entry fee); or (c) the host is paid (Hestiia, France, €450/yr per house). Consumer-owned crypto heaters (Qarnot QC-1, Heatbit) push electricity cost and mining risk onto the buyer.

### Cited Findings

**Qarnot (France)**
- For the Bordeaux/Gironde QH-1 deployment, DCD reports that HPC tasks are sent to the heaters and "Qarnot pays for the electricity used, so the heat is free" (search snippet; the page returned 403) — [DCD, "Bordeaux buys distributed cloud heaters"](https://www.datacenterdynamics.com/news/bordeaux-buys-distributed-cloud-heaters/)
- 346 QH-1 heaters in Bordeaux heat two floors of public offices and four floors of social housing (49 apartments) "for free" while computing for banks, 3D studios and research labs (date not captured) — [Solar Impulse case study](https://solarimpulse.com/solutions-explorer/implementation-stories/qarnot-qh-1-adopted-by-departement-de-la-gironde-in-bordeaux-for-sustainable-heating-solution)
- Next.ink (10 Jul 2026) describes Qarnot's heaters as placing compute hardware (including crypto-mining) in homes "with heating provided free to occupants". Some landlords and developers adopted them with "résultats mitigés", with Gironde Habitat given as an example — [Next.ink](https://next.ink/247072/scaleway-rachete-qarnot-et-ses-activites-hpc-recemment-placees-en-redressement-judiciaire)
- QC-1 crypto heater (Mar 2018): sold to consumers at €2,900 plus shipping. Up to 500 W (650 W in boost mode). Qarnot estimated ~$120/month of Ether "before electricity costs", so the buyer pays the power and keeps the crypto — [Tom's Hardware](https://www.tomshardware.com/news/qarnot-qc-1-crypto-heater,36654.html); [TechCrunch 2018-03-08](https://techcrunch.com/2018/03/08/qarnot-unveils-a-cryptocurrency-heater-for-your-home)
- By 2023 Qarnot was selling heat. Clients included social landlords, property developers, local authorities, swimming pools and heating-network operators. Founder quote: "It runs computers and it sells heat, which is great for the company's bottom line." Heat pricing was not disclosed — [TechCrunch 2023-01-09](https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/)

**Deep Green (UK)**
- "The host site gets free heat". Deep Green covers installation, maintenance and IT operating costs, and the host's own boiler only tops up (16 Jan 2024) — [The Register](https://www.theregister.com/2024/01/16/deep_green_gets_200m_from/)
- Sources disagree on how the electricity is paid. Capacity Media says the leisure centre's electricity costs for the "digital boiler" "will also be refunded" — [Capacity Media](https://www.capacitymedia.com/article/2bk13yjhuj9qedmkvxszk/news/deep-green-repurposes-data-centre-heat-to-heat-public-swimming-pool). DCD says Deep Green "pays for the electricity it uses and gives the heat free" — [DCD](https://datacenterdynamics.com/en/news/uk-data-center-startup-offers-to-heat-britains-swimming-pools-with-waste-heat). Either way, Deep Green bears the electricity cost.
- Lansing, Michigan proposal (Nov 2025 to Apr 2026): the 24 MW facility would give carbon-neutral heat to the Lansing Board of Water & Light's hot-water system, and "in return, the utility would supply the facility's power" — [The State News, 2026-04-06](https://statenews.com/article/2026/04/proposed-lansing-data-center-scrapped-hours-before-council-meeting)

**Cloud&Heat / AoTerra (Germany, Dresden)**
- AoTerra (Dresden): building owners paid about €12,000 up front, and "Strom- und Wasserkosten übernimmt Ao Terra für 15 Jahre" (AoTerra covers electricity and water for 15 years), as well as upkeep. Broadband of at least 50 Mbit/s was required (29 Aug 2013, updated 31 Jan 2014) — [Netzwoche](https://www.netzwoche.ch/news/2014-01-31/heizen-mit-der-cloud)
- "Cloud&Heat pays the Internet and electricity bills for the unit" (search snippet) — [eWeek](https://www.eweek.com/servers/german-company-offers-to-heat-homes-with-cloud-servers/)

**Nerdalize (Netherlands)**
- 2015 Eneco trial in 5 homes. Sources differ on who paid for power: one says Nerdalize paid the electricity, another says "Eneco will cover all computing-related energy costs". Households were expected to save about €400/yr on heating (Eneco spokesman Marcel van Dun) — [PCWorld](https://www.pcworld.com/article/432611/server-heating-startup-teams-with-energy-company-to-heat-dutch-homes.html); [Computerworld](https://www.computerworld.com/article/1636612/its-a-server-no-its-a-radiator.html)
- 2017 hot-water model: "Households pay an entrance fee of 400 euros and after that their heating is free". Savings were quoted at up to €300/yr, and Nerdalize paid the electricity (search summaries) — [Digital Trends](https://www.digitaltrends.com/home/crowdfunded-water-heater-will-save-bundle-utilities-bill/); [DCD, Nerdalize raises €700k](https://www.datacenterdynamics.com/en/news/nerdalize-raises-700k-for-distributed-heat-systems/)

**Leafcloud (Netherlands)**
- "The power consumed by the servers is metered and paid by Leafcloud." Leafcloud owns all the equipment and covers installation, maintenance and replacement. The host provides space (10-50 m²), a power connection, water-loop access and fibre if available. In return the host gets "free baseload heat" of 630-3,780 GJ/yr. No rent, cash payment or revenue share is mentioned. Example: a Zaandam nursing home saves €6,000/yr in avoided gas (company page, accessed Nov 2026) — [Leafcloud Leaf sites](https://www.leaf.cloud/leafsites/)

**Other / baseline**
- Heata (UK) "pays for additional electricity used by the mini server" (search snippet) — [TechRadar](https://techradar.com/pro/this-new-uk-domestic-data-furnace-from-heata-can-convert-cloud-computing-waste-heat-into-free-hot-water)
- Hestiia (France), myEko radiator (6 Apr 2023): the homeowner buys radiators (€490 pre-order, then €590 each) and receives an annual hosting payment, "up to €450 a year for a 90m² house with four or five radiators". The compute is sold over the home's wifi. The article does not say who pays the electricity — [Connexion France](https://www.connexionfrance.com/practical/get-paid-to-heat-your-french-home-with-it-processing-radiators/151943)
- Heatbit (consumer crypto heaters): the consumer buys the device (Maxi ~$1,249; Bitwater water-heater element $899, launched Oct 2026) and pays the power while mining bitcoin — [Bob Vila review](https://www.bobvila.com/reviews/heatbit-maxi-review/); [Decrypt](https://decrypt.co/381665/heatbits-899-water-heater-element-mines-bitcoin-while-it-heats-your-tank?amp=1)

### Inferences
- In this market, "operator pays electricity, host gets heat free" is the standard deal. A Swiss host will expect it as a baseline. Deals that asked the host for money (AoTerra €12k, Nerdalize €400) belong to companies that later exited or failed. That is a correlation, not proof of cause.
- When a utility is the counterparty (Eneco 2015; Lansing BWL power-for-heat), the electricity cost can be swapped against the heat value. This is a possible structure for DigitalHeat with Swiss EVUs/Stadtwerke.
- Consumer crypto heaters are a different business (hardware sales). They put electricity-price and crypto-price risk on the household, and they do not tell us much about a B2B basement-rack model.

### Gaps
- No source found confirming a Qarnot deal specifically with **Paris Habitat** or its billing terms. A ~2015 item mentions a Paris 15th-arrondissement public housing agency choosing Q.rads, without naming it — [Business Day Ghana](https://businessdayghana.com/?p=3820) (low-quality source).
- How Qarnot measured and paid electricity in tenants' flats (separate meter vs. reimbursement) was not found.
- Deep Green: whether it pays the utility directly or refunds the host could not be resolved from primary documents.
- Leafcloud: contract length and any heat-pricing schedule are not public.

---

## 2. Unit size (kW per site), installation location, heat temperature

### Takeaway
Unit sizes cluster in three tiers: ~0.5-1 kW room heaters (Qarnot Q.rad/QC-1, Hestiia, Heatbit), ~5-120 kW building/basement systems (Cloud&Heat, Nerdalize boilers, Leafcloud 20-120 kW, Deep Green pool pilots), and 100 kW to 24 MW boiler or data-centre installations (Qarnot boilers and data centres, Blockheating 200 kW, Deep Green 5-24 MW). Delivered temperatures of 45-65 °C are typical for liquid cooling. Only Empa's lab reports 70 °C.

### Cited Findings
- **Qarnot**: QC-1 up to 500 W (650 W in boost), sized for 20 m² — [Tom's Hardware](https://www.tomshardware.com/news/qarnot-qc-1-crypto-heater,36654.html). Boiler modules hold up to 12 servers. The Finland heating-network pilot is 100 kW of compute, and Qarnot is targeting sites of 500 kW to a few MW (Jan 2023) — [TechCrunch](https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/). An Italian data centre with A2A (Jun 2025) produces 16 GWh/yr of heat, enough for ~1,350 apartments, via district heating — [BeBeez](https://bebeez.eu/2025/06/26/qarnot-launches-italian-data-center-waste-heat-to-be-used-in-local-district-heating-network/)
- **Deep Green**: Exmouth pool pilot expected 139,284 kWh/yr of heat, 62% of the pool's needs, saving >£20,000/yr. Hardware is described inconsistently as "12 four-CPU cards" or "a 50-kilowatt data centre", immersed in mineral oil (2023) — search summaries citing [DCD](https://datacenterdynamics.com/en/news/uk-data-center-startup-offers-to-heat-britains-swimming-pools-with-waste-heat) and [The Register 2023-03-14](https://www.theregister.com/2023/03/14/cloud_startup_waste_heat_dcs/). Later projects: a 5 MW Bradford plan (Jul 2025), the Urmston, Manchester AI colocation (Mar 2026), and Lansing 24 MW (withdrawn Apr 2026) — [DCD company page](https://www.datacenterdynamics.com/en/company/Deep-Green/); [IT Brief UK](https://itbrief.co.uk/story/deep-green-opens-rapid-ai-ready-colocation-in-manchester); [The State News](https://statenews.com/article/2026/04/proposed-lansing-data-center-scrapped-hours-before-council-meeting)
- **Cloud&Heat**: direct liquid-cooled racks in secure cabinets inside residential buildings. Sites included Wallotstraße and Tannenstraße in Dresden — [Cloud&Heat, 2025-01-20](https://www.cloudandheat.com/en/news-press/once-upon-a-time-there-was-a-cloud-that-heated-homes-worldwide/). One reference was a new 56-flat block with a data centre in the basement (search summary) — [Computerwoche](https://www.computerwoche.de/a/rechenzentrum-heizt-oeffentliches-hallenbad,1860074)
- **Nerdalize**: the 2015 e-Radiator heated a closed water loop to 45-55 °C. Excess heat could be dumped through an outdoor heat expeller — [Computerworld](https://www.computerworld.com/article/1636612/its-a-server-no-its-a-radiator.html). The 2017 units fed domestic hot water and central heating — [DCD](https://www.datacenterdynamics.com/en/news/nerdalize-raises-700k-for-distributed-heat-systems/)
- **Leafcloud**: LS-20/40/80/120 models (modular 20 kW blocks), 20-120 kW IT load, 45-65 °C output, sized at 5-20% of the building's design thermal load. Hosts must have at least 500 GJ/yr of hot-water demand, three-phase power and existing hot-water infrastructure. Zaandam is a 5 kW site. Building types include pools, apartment buildings, care homes, hospitals, offices, schools, district heating and ATES. Time to heat delivery is 3-6 months — [Leafcloud](https://www.leaf.cloud/leafsites/)
- **Blockheating (NL)**: 200 kW containerised edge data centres delivering 65 °C water to greenhouses. A 60 kW prototype was installed at a tomato greenhouse in 2019 — [DCD](https://www.datacenterdynamics.com/en/news/itrenew-and-blockheating-combine-edge-data-centers-greenhouses)
- **Windcloud (DE)**: exhaust at ~35.9 °C heats a 240 m² rooftop algae farm (2019-2021 coverage) — [Netzwoche 2020](https://www.netzwoche.ch/news/2020-09-06/warum-in-einem-nordfriesischen-rechenzentrum-algen-wachsen)
- **Swiss examples**: Empa NEST (Dübendorf) has a basement micro data centre that has fed the low/medium-temperature heating network for ~2 years. Liquid cooling (Zutacore, EU HEATWISE project, 2024-2027) aims for up to 70 °C into the high-temperature network for showers. No kW given, and the business model is not covered (14 Apr 2024) — [Netzwoche/Empa](https://www.netzwoche.ch/news/2024-04-14/waerme-aus-dem-rechner). Infomaniak's D4 data centre in Geneva feeds district heating for ~6,000 households — [ABB](https://new.abb.com/news/de/detail/124445/abgesichert-mit-usv-von-abb-infomaniak-rechenzentrum-wird-tausende-genfer-haushalte-heizen)

### Inferences
- DigitalHeat's 5-20 kW at 50-70 °C sits at the low end of Leafcloud's range (20-120 kW, 45-65 °C) and around the size of the Zaandam site (5 kW). Leafcloud is the closest live comparator. The upper end of DigitalHeat's 70 °C target is above most operators' stated output. Only Empa's lab system claims 70 °C.
- Over time, the operators that survived moved to larger units (Qarnot from heaters to boilers to data centres; Deep Green from pool pilots to MW sites). That suggests per-site fixed costs (install, connectivity, maintenance) hurt at small kW.

### Gaps
- No primary spec found for a "QH-1" power rating or the "QB" boiler kW per module.
- Deep Green's per-pool kW is reported inconsistently, and the current number of live pool sites is not public.

---

## 3. Compute customers, pricing, and summer / no-heat periods

### Takeaway
Compute customers were mainly batch/HPC (banks, animation studios, research) for Qarnot, general cloud/colocation and AI for Deep Green and Leafcloud, and storage/VMs for Cloud&Heat and Nerdalize. None published per-unit pricing in the sources found. For summer, operators either put units where heat demand runs all year (hot water, pools, district heat, greenhouses) or dump the heat (Nerdalize's outdoor expeller; Microsoft's year-round Data Furnace venting outside).

### Cited Findings
- **Qarnot** customers: BNP Paribas, Société Générale and the 3D studio Illumination rented servers (Jan 2023) — [TechCrunch](https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/). Banks, 3D animation studios and research labs (Jun 2017). Software balanced client compute against residents' temperature needs — [EU Horizon Magazine](https://projects.research-and-innovation.ec.europa.eu/en/horizon-magazine/radiators-powered-excess-computing-energy-are-heating-homes-free)
- **Qarnot** revenue: €2.68M (2023) and €3M (2024). Cumulative losses of €9M over 2023-2024 — [Next.ink](https://next.ink/247072/scaleway-rachete-qarnot-et-ses-activites-hpc-recemment-placees-en-redressement-judiciaire)
- **Deep Green** rents cloud compute to businesses. A post-production company committed to its Devon data centre — [Computer Weekly](https://www.computerweekly.com/news/366571793/Post-production-company-to-go-all-in-on-Deep-Greens-heat-reusing-datacentre-in-Devon). Lansing would have leased server space including to AI companies — [The State News](https://statenews.com/article/2026/04/proposed-lansing-data-center-scrapped-hours-before-council-meeting)
- **Leafcloud** markets a public cloud plus GPUs, with "Dynamic GPU Pricing" and a free GPU tier. No numbers were on the page — [Leafcloud Truly Green](https://www.leaf.cloud/truly-green). It plans NVIDIA Blackwell RTX PRO 6000 GPUs from Q1 2026, a "5x" increase in AI capacity heating ~2,000 households (press release, 20 Nov 2025; from search summary because the page was behind a bot check) — [Emerce](https://www.emerce.nl/wire/leafcloud-vervijfvoudigt-aicapaciteit-levert-daarmee-warmte-2000-huishoudens)
- **Cloud&Heat/AoTerra** sold or rented the servers to companies as cloud storage or VM hosts, stressing that data stayed in Germany — [Netzwoche](https://www.netzwoche.ch/news/2014-01-31/heizen-mit-der-cloud)
- **Nerdalize** sold cheap compute and storage services to businesses — [Silicon Canals](https://siliconcanals.com/news/innovative-e-radiator-startup-nerdalize-files-for-bankruptcy-another-painful-end-in-dutch-startup-ecosystem/)
- **Hestiia**: demand for compute came "mostly from developers of artificial intelligence systems and blockchain applications" (2023) — [Connexion France](https://www.connexionfrance.com/practical/get-paid-to-heat-your-french-home-with-it-processing-radiators/151943)
- **Summer handling**:
  - Nerdalize dumped excess heat through an outdoor heat expeller — [Computerworld](https://www.computerworld.com/article/1636612/its-a-server-no-its-a-radiator.html)
  - Microsoft's 2011 Data Furnace paper proposed seasonal units using decommissioned servers for batch jobs, alongside year-round units that vent heat outside in summer (summary) — [Data Center Knowledge](https://www.datacenterknowledge.com/business/data-furnaces-crazy-idea-or-practical-solution-); [MSR publication](https://www.microsoft.com/en-us/research/publication/the-data-furnace-heating-up-with-cloud-computing/)
  - Leafcloud targets "continuous" hot-water baseload (630-3,780 GJ/yr, 24/7) — [Leafcloud](https://www.leaf.cloud/leafsites/)
  - Blockheating's greenhouse unit heats 2 ha in summer vs 0.5 ha in winter (search summary) — [DCD](https://www.datacenterdynamics.com/en/news/itrenew-and-blockheating-combine-edge-data-centers-greenhouses)

### Inferences
- Revenue per site is small. Qarnot reached only ~€3M revenue a year after more than a decade and €35M raised in 2023, which points to thin compute margins at distributed scale.
- Year-round hot-water baseload (Leafcloud, Heata, Nerdalize 2017, pools) is the main answer to the summer problem. DigitalHeat's hot-water component matters more than space heating for utilisation.

### Gaps
- No published per-hour or per-kWh compute prices for any comparator. Leafcloud's pricing page was not read.
- How Qarnot throttled compute in summer in housing deployments was not found.

---

## 4. Funding, scale, current status (Nov 2026), and stated reasons for pivots or failure

### Takeaway
None of the residential-scale pioneers survived on that model. Nerdalize went bankrupt (Dec 2018). Cloud&Heat said the business model "ultimately proved unsuccessful" and shut its residential sites. Qarnot entered redressement judiciaire (May 2026) and was sold to Scaleway (Jul 2026) after pivoting to boilers and data centres. Deep Green is alive but has moved to MW-scale colocation. Leafcloud is the remaining building-hosted operator, still small and seed-funded.

### Cited Findings

**Qarnot**
- Funding: ~$6.5M (2020) on top of $2.5M from Data4 (search summary) — [DCD, EIC funding](https://datacenterdynamics.com/en/news/hpc-cloud-provider-qarnot-gets-funding-from-european-innovation-council). €12.5M equity plus a €22.5M credit line in Jan 2023 (Société Générale Ventures, ADEME Investissement, Demeter, Banque des Territoires, Colam Impact) — [TechCrunch](https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/). EIC funding in 2025 — [DCD](https://datacenterdynamics.com/en/news/hpc-cloud-provider-qarnot-gets-funding-from-european-innovation-council)
- Status: the Tribunal des activités économiques de Nanterre opened redressement judiciaire on 19 May 2026. Scaleway (Iliad) acquisition announced 10 Jul 2026, likely a prepack. The €35M "did not balance the accounts", and a quiet capital increase in early 2025 did not prevent the procedure — [Next.ink](https://next.ink/247072/scaleway-rachete-qarnot-et-ses-activites-hpc-recemment-placees-en-redressement-judiciaire); [Scaleway press release](https://www.scaleway.com/en/news/scaleway-acquires-qarnot-to-strengthen-its-european-cloud-and-ai-platform-with-low-carbon-hpc-technology/). Terms undisclosed — [TelecomTV](https://www.telecomtv.com/content/ai/what-s-up-with-iliad-s-scaleway-drivenets-a1-55863/amp/)
- Pivot path: heaters for builders, then QC-1 crypto heater (2018), then "QBx" boiler clusters for heating networks (2023), then data centres feeding district heat (Italy, 2025) — [TechCrunch 2023](https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/); [BeBeez](https://bebeez.eu/2025/06/26/qarnot-launches-italian-data-center-waste-heat-to-be-used-in-local-district-heating-network/)

**Deep Green**
- £200M from Octopus Energy Generation (Octopus Energy Transition Fund and Sky ORI fund), "likely spread over several years", for 100-150 pool deployments (16 Jan 2024) — [The Register](https://www.theregister.com/2024/01/16/deep_green_gets_200m_from/); [Octopus press release](https://octopus.energy/press/deep-green-investment/)
- 2025-26: Lansing 24 MW / $120M announced Nov 2025 — [BeBeez](https://bebeez.eu/2025/11/10/deep-green-plots-us-expansion-announces-24mw-data-center-in-michigan/). Withdrawn 6 Apr 2026, hours before the council vote, after opposition. Search summaries mention questions about Deep Green's finances, but The State News article itself raises none. CEO is now Mark Lee — [The State News](https://statenews.com/article/2026/04/proposed-lansing-data-center-scrapped-hours-before-council-meeting); [Michigan Advance](https://michiganadvance.com/2026/04/06/deep-green-pulls-request-to-rezone-downtown-lansing-parcel-axing-data-center-proposal/) (not fetched, 403). Manchester AI colocation launched Mar 2026 — [IT Brief UK](https://itbrief.co.uk/story/deep-green-opens-rapid-ai-ready-colocation-in-manchester)

**Cloud&Heat**
- Founded 2011 as a TU Dresden spin-off. After more than 10 years it is decommissioning its Wallotstraße and Tannenstraße micro data centres: "While the approach was technologically convincing, the business model associated with this innovation ultimately proved unsuccessful." The closures were "economically driven". Strategic realignment came at the turn of 2022/23, with the WAIYS GmbH spin-off in autumn 2023. Focus is now Managed Kubernetes and on-prem (Proxmox partner in 2026) (20 Jan 2025) — [Cloud&Heat](https://www.cloudandheat.com/en/news-press/once-upon-a-time-there-was-a-cloud-that-heated-homes-worldwide/)
- AoTerra (Dresden) raised ~€1M by crowdfunding and targeted 100 systems by end-2013 and 500 in 2014 — [Netzwoche](https://www.netzwoche.ch/news/2014-01-31/heizen-mit-der-cloud)

**Nerdalize**
- Eneco was an investor and supplied servers until end-2016. Other investors offered up to €850k. A 2017 crowdfunding raised €750k. 2017 loss of at least €882k, negative equity, and obligations to repay part of €2M in loans by end-2019. "No information regarding the causes of bankruptcy" was given; speculation pointed to insufficient demand — [Silicon Canals, 2019-01-02](https://siliconcanals.com/news/innovative-e-radiator-startup-nerdalize-files-for-bankruptcy-another-painful-end-in-dutch-startup-ecosystem/)
- Bankruptcy filed/declared 27 Dec 2018. Neither the company nor the curator gave a reason — [NL Times](https://nltimes.nl/2019/01/02/startup-using-servers-heat-homes-files-bankruptcy). A later roundup cites "unsustainable losses" and payment arrears to supplier Amacom as the trigger (search summary, not read directly) — [MT/Sprout](https://mtsprout.nl/groei/deze-ondernemers-gingen-2019-failliet). A restart (doorstart) was reported — [Bits&Chips](https://bits-chips.com/artikel/doorstart-voor-nerdalize/)

**Leafcloud**
- Seed round with The Sharing Group (CB Insights dates it 21 Jan 2025, amount undisclosed). NVIDIA Inception member — [CB Insights](https://www.cbinsights.com/company/leafcloud/financials); [Silicon Canals](https://siliconcanals.com/the-sharing-group-acquires-stake-in-leafcloud/). AI capacity expansion from Q1 2026, focused on Amsterdam — [Emerce](https://www.emerce.nl/wire/leafcloud-vervijfvoudigt-aicapaciteit-levert-daarmee-warmte-2000-huishoudens) (search summary)

**Others**
- Heatbit: private, still shipping (Bitwater launched Oct 2026) — [Forklog](https://forklog.com/en/heatbit-unveils-water-heater-with-bitcoin-mining-capability/)
- Blockheating, Windcloud: no 2025-26 status found.

### Inferences
- Company outcomes so far: residential/home units failed (Nerdalize, Cloud&Heat residential, Qarnot housing "mitigated" and later insolvent). Large heat-network or colocation projects attract big capital (Octopus £200M, Qarnot €35M) but have not been proven profitable. Building-scale B2B hosting with free heat (Leafcloud) survives at small scale.
- In 2026, the buyer of Qarnot's assets was a cloud provider buying HPC capability and a sustainability story, not a heat business. The compute business is where acquirers saw value.

### Gaps
- No primary account of Qarnot's specific reasons for insolvency, or whether housing heaters were part of the assets sold.
- Deep Green's revenue, number of live pools, and how much of the £200M has been drawn are not public.
- Leafcloud's site count, revenue and round size are undisclosed. CB Insights gives conflicting founding years (2020/2022).

---

## 5. Lessons explicitly drawn by founders, analysts or research

### Takeaway
Few founders have published explicit post-mortems. The clearest statement is Cloud&Heat's ("technologically convincing", business model "ultimately proved unsuccessful", closures "economically driven"). Analysts and the original Microsoft paper point to the same pressures: electricity cost borne by the operator, per-site overhead, broadband and owner trust, and the need for year-round heat demand.

### Cited Findings
- Cloud&Heat: "technologically convincing … business model … ultimately proved unsuccessful". Decommissioning was "economically driven" (2025) — [Cloud&Heat](https://www.cloudandheat.com/en/news-press/once-upon-a-time-there-was-a-cloud-that-heated-homes-worldwide/)
- Qarnot founder Paul Benoit: "The big issue with data centres is all the heat generated. And the biggest problem with homes is how to heat them." (2017) — [Horizon Magazine](https://projects.research-and-innovation.ec.europa.eu/en/horizon-magazine/radiators-powered-excess-computing-energy-are-heating-homes-free). By 2023 the pitch was: "you don't need a cooling system and we can sell the heat" — [TechCrunch](https://techcrunch.com/2023/01/09/qarnot-creates-green-data-centers-by-putting-servers-in-central-heating-boilers/)
- Next.ink says landlord adoption of Qarnot heaters gave "résultats mitigés" (Gironde Habitat) and that €35M raised "did not balance the accounts" (2026) — [Next.ink](https://next.ink/247072/scaleway-rachete-qarnot-et-ses-activites-hpc-recemment-placees-en-redressement-judiciaire)
- Silicon Canals (2019) speculated that Nerdalize failed on "insufficient demand for the heating product" — [Silicon Canals](https://siliconcanals.com/news/innovative-e-radiator-startup-nerdalize-files-for-bankruptcy-another-painful-end-in-dutch-startup-ecosystem/)
- TechCrunch's 2011 critique of the Data Furnace pointed to electricity cost increases of several thousand dollars per furnace, homeowner trust and broadband (search summary) — [TechCrunch](https://techcrunch.com/?p=397160); [MSR paper](https://www.microsoft.com/en-us/research/publication/the-data-furnace-heating-up-with-cloud-computing/)
- BFE (Swiss Federal Office of Energy) material notes that mixed-use areas (housing plus commerce/industry) allow better use of waste heat (search summary) — [BFE pubdb](https://pubdb.bfe.admin.ch/de/publication/download/11426)

### Inferences (for DigitalHeat)
- **Deal structure that holds up:** the operator owns the hardware, pays metered electricity, and gives baseload hot-water heat free or at a discount to a professional building owner (cooperative, Verwaltung, care home, pool). This is the Leafcloud/Heata/Deep Green pattern. Asking hosts for capex (AoTerra) or entry fees (Nerdalize) did not scale.
- **Hot water before space heat:** year-round domestic hot water and pools avoid the summer-idle problem that Microsoft's paper and Nerdalize ran into.
- **Compute is the business:** heat value covers at most cooling and some site cost. Qarnot's ~€3M revenue on years of funding, and its sale to a cloud provider, show that compute demand and utilisation decide survival. Contracted AI/batch demand matters more than heat contracts.
- **Avoid sub-5 kW and in-flat units:** the move by every survivor to larger units suggests per-site overhead dominates at small kW. A 5-20 kW basement rack is roughly at the minimum viable size. Leafcloud's smallest catalogue unit is 20 kW, though it does run a 5 kW site.
- **Utility partnership as an option:** a utility/EVU supplying power in exchange for heat (Lansing BWL concept; Eneco 2015) is a possible Swiss structure, but neither example reached operation at scale.

### Gaps
- No public Swiss operator of distributed basement compute-heat was found. Searched for "DigitalHeat" public material, Green.ch heat reuse (a press PDF exists but was not read: [Green.ch PDF](https://Green.ch/fileadmin/user_upload/Pressespiegel/DE/GR_CL_2023_09_Faktor_Waerme_aus_dem_Server.pdf)), and Swisscom heat reuse (not searched successfully). Swiss examples found are data-centre to district-heat (Infomaniak Geneva) and research (Empa NEST).
- No founder post-mortem from Nerdalize or Qarnot was found.
- Thermal Grid (NL) was not found in search results. Heatbit and Windcloud business-model economics are undocumented.

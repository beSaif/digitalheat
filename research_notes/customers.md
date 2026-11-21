# Customers for DigitalHeat: who needs heat all year, and who also needs local compute

Research notes for the sprintd Basel DigitalHeat case. Team Ctrl+Free, November 2026.

**The question:** a DigitalHeat server delivers roughly 1 kW of heat as 50–60 °C water, with no heat pump. Homes need very little heat in summer. Which customers need 50–60 °C heat all year, ideally during office hours too, and which of them also need private, on-site compute?

**Conventions**
- Every number has a link to its source.
- **(est.)** marks our own arithmetic or assumptions. These are not quoted figures.
- **Servers needed (est.)** = average annual heat ÷ 8.76 MWh. That is what one 1 kW server gives off if it runs 24/7 all year. Peak load is higher, so read this as the server count that covers base load.

---

## TL;DR

- **Best fit on temperature and load profile:**
  - Indoor pools and spas: water at 28–36 °C, 24/7, all year.
  - Pharma HVAC/cleanroom reheat: supply at 50–60 °C, 24/7.
  - Herb, seed and malting-grain drying: 40–55 °C.
  - Greenhouses: KEZO Hinwil runs on a 45 °C supply.
  - Archive/museum depots: low-temperature heating, plus summer dehumidification. Desiccant wheels regenerate well at 50–60 °C.
- **Partial fit (pre-heat only):**
  - Hot water in hospitals, hotels and care homes: legionella rules need 60 °C at the tank and 55 °C in the loop.
  - Laundries: 60–75 °C washes.
  - Dairy and brewery CIP and pasteurisation: 63–90 °C.
  - Pharma hot water for injection (WFI) loops: 65–80 °C.

  The server loop can pre-heat these from about 10 °C to 50–55 °C, which is most of the temperature lift. A booster supplies the last 5–30 K.
- **Summer heat sinks that complement homes:** hay drying (May–Sep), outdoor pools, and archive dehumidification on humid summer days.
- **Top 5 "one customer, two needs" pilots:**
  1. Universitätsspital Basel
  2. A mid-size Basel-area pharma/biotech R&D site (Bachem, Idorsia, or tenants at Switzerland Innovation Park Basel Area)
  3. Kanton Basel-Stadt: IT BS AI platform, plus public pools and the new natural history museum and state archive building opening in 2028
  4. Universität Basel / sciCORE+
  5. A transport operator: BLT/BVB depots plus on-site bodycam video processing

  Details are in Part 2.

---

## Part 1: Businesses that need 50–60 °C heat all year (Switzerland, Basel first)

### 1.1 Segment overview

| Segment | Heat used for | Temperature needed | Fit with 50–60 °C | Load profile | Heat demand per site | Servers needed (est.) |
|---|---|---|---|---|---|---|
| **Pharma & biotech** | HVAC reheat and cleanroom air handling; process air after dehumidification; CIP; WFI/purified-water loops; lab buildings | HVAC heating circuits supplied at **50–60 °C** ([Cerbios pinch study, EnergieSchweiz 2020](https://pubdb.bfe.admin.ch/en/publication/download/10198)). Fluid-bed dryer air reheated to **70 °C** after dehumidifying at 3 °C (same source). Water-system sanitisation at **65–80 °C** per USP <1231> ([GMP-Compliance](https://www.gmp-compliance.org/gmp-news/what-is-the-optimal-temperature-for-sanitizing-water-systems)) | **HVAC: full fit.** CIP and WFI: pre-heat only | 24/7, all year. Cleanroom HVAC runs continuously at very high air-change rates. HVAC can exceed half of a plant's electricity, and cleanrooms use up to 15× the energy of commercial buildings ([ISPE](https://ispe.org/pharmaceutical-engineering/september-october-2021/pharmaceutical-cleanroom-design-iso-14644-16)) | Cerbios-Pharma (Lugano): **5.6 GWh/a gas**, of which **45 % goes to heating and ventilation** because of strict air-quality rules ([BFE 10198](https://pubdb.bfe.admin.ch/en/publication/download/10198)). Novartis Campus St. Johann reference demand: **90 GWh/a heat** ([PSI 2003, Hirschberg et al.](https://www.psi.ch/ta/PublicationTab/Comparison_of_Energy_Supply_Options_for_Novartis_C.pdf)) | Cerbios HVAC share ≈ 2.5 GWh ⇒ **~290 servers**. Novartis Campus ⇒ **~10,000** (est.) |
| **Indoor pools, spas, thermal baths** | Pool water make-up and losses, hall air (high humidity), showers | Pool water about **30 °C** ([Exmouth / BBC via Yahoo](https://uk.news.yahoo.com/data-centre-used-heat-25-162657316.html)). Brine spa water **33–34 °C**, hot tub **36–38 °C** (sole uno, [badi-info](https://www.badi-info.ch/a/rheinfelden-sole-uno.html)). Thermal pools **34–36 °C** (Zurzach, [Kanton AG](https://www.ag.ch/umwelt-aargau/pdf/UAG_So_15_35.pdf)) | **Excellent.** Well below 50 °C, so the return water stays cool. Showers need 60 °C (pre-heat) | 24/7 losses all year; opening hours about 07–22. Already proven with servers: Deep Green covers **62 %** of Exmouth's pool heat (**139,284 kWh/a**) ([DCD](https://datacenterdynamics.com/en/news/uk-data-center-startup-offers-to-heat-britains-swimming-pools-with-waste-heat), [Wigan FOI](https://www.wigan.gov.uk/Docs/PDF/Council/Disclosure-Logs/2023/March/14816.pdf)) | Hallenbad Allschwil BL: heat **1,100 MWh/a before renovation, 627 MWh/a after** ([BFE case study](https://pubdb.bfe.admin.ch/de/publication/download/816)). Exmouth gas demand ≈ **222 MWh/a** (Wigan FOI) | Allschwil ⇒ **~70 servers** (est.) |
| **Agriculture: greenhouses** | Space heating of glasshouses, mostly at night (see the BDEW horticulture profile, Part 3) | KEZO Hinwil greenhouse: **45 °C supply**, 39,000 m², 7.5 MW ([BFE 4800](https://pubdb.bfe.admin.ch/de/publication/download/4800)) | **Excellent** | Heating season plus cool nights, about Sep–May. Night-heavy, so it complements office loads | Tomatoes: **270–350 kWh/m² per crop** (standard greenhouse, Agroscope Conthey, [table](https://www.newsd.admin.ch/newsd/message/attachments/18242.pdf)) | 1 ha of tomatoes ≈ 3 GWh ⇒ **~340 servers** (est.) |
| **Agriculture: drying** | Hay ventilation; grain, seed and malting-barley drying; herb drying; wood-chip drying | Herbs with essential oils **40–50 °C**. Seed and malting barley **45–55 °C**. Wood chips best **below 50–60 °C** (above that, volatiles are lost) ([FNR Materialienband](https://news.fnr.de/fileadmin/fnr/pdf/Materialienband_final.pdf)). Hay warm-ventilation needs only a few K of air warming ([Agroscope guideline](https://lfl.bayern.de/mam/cms07/ilt/dateien/agroscope_transfer_38_2014_richtlinien_f%C3%BCr_heubel%C3%BCftungsanlagen.pdf), [Swissmilk / Schweizer Bauer](https://api.swissmilk.ch/wp-content/uploads/2019/05/futterkonservierung-zuegig-heuen-dank-belueftung-artikel-schweizer-bauer-15-Mai-2021-de.pdf)) | **Excellent** for herbs, seed grain, chips and hay. Food grain (60–110 °C): partial | **Summer and harvest season** (May–Oct). This is the mirror image of home heating | Per farm: seasonal, tens to hundreds of MWh (est.) | Seasonal (est.) |
| **Agriculture: vertical farming** | Hall heating to about 25 °C | Hall air about **25 °C** ([myclimate on YASAI](https://www.myclimate.org/en/information/news-press/news/newsdetail/herbs-of-the-future-yasai-breaks-new-ground-with-vertical-farming-1/)) | Fit, but LED waste heat often already covers it | 24/7 | YASAI Niederhasli: 1,100 m² (same source) | Small |
| **Museum & archive depots** | Gentle heating; reheat after cooling dehumidification; desiccant-wheel regeneration | Depot target **18 ± 2 °C, 50 ± 5 % RH** ([FH Potsdam / Landesfachstelle](https://FH-potsdam.de/sites/default/files/2022-05/landesfachstelle-archivberatung-bestandserhaltung-klimamessung-und-klimaregulierung-archivmagazin-fhpotsdam.pdf)). Augusta Raurica tolerates 14–27 °C ([Klimakonzept](https://www.augustaraurica.ch/assets/content/files/06_Ueber-uns/JbAK46_Klimakonzept-des-Sammlungszentrums.pdf)). Silica-gel wheels: optimum regeneration about **50–60 °C** ([J. Thermal Eng.](https://doi.org/10.18186/thermal.1332521), [CSITE 2025](https://www.open-access.bcu.ac.uk/16753/1/1-s2.0-S2214157X25002333-main.pdf)) | **Excellent** (low-temperature) | 24/7, all year. **Summer dehumidification is a summer heat sink** | Small per site (est. tens to hundreds of MWh). Value lies in stability and 24/7 operation | 5–30 (est.) |
| **Laundries** | Wash water, rinsing, drying, ironing | Wash at **60–75 °C**. Heating 10→75 °C takes 271.8 kJ per litre ([Laundry & Cleaning News](https://laundryandcleaningnews.com/?p=16128)) | **Pre-heat** to about 55 °C covers about 70 % of the temperature lift (est.) | One or two weekday shifts. Saturday about 0.39× a weekday (BDEW GWA, Part 3) | Unit use **1.0–1.5 kWh/kg** (Laundry & Cleaning News). bardusch Basel (ex-Zentralwäscherei Basel): **85–100 t/day** ([bardusch](https://www.bardusch.com/fileadmin/Switzerland/Presse/2017-Hightech-Waescherei/Bardusch_Medienmitteilung_Einweihung_Privatwaescherei.pdf)) | 100 t/d × 1.2 kWh/kg ≈ 120 MWh/d ⇒ **~5,000 servers** if all heat came from servers (est.). Realistic share: pre-heat only |
| **Food & beverage** | Pasteurising, CIP, brewing water, bottle washing, cheese-making milk heating | HTST pasteurisation **72–75 °C**, thermisation **63–65 °C** ([Tetra Pak handbook](https://dairyprocessinghandbook.tetrapak.com/chapter/heat-exchangers)). CIP **41–91 °C** ([solar process heat table](https://www.crses.sun.ac.za/files/services/events/workshops/01_Solar%20Heat%20for%20Industrial%20Processes%20_Overview_Weiss.pdf)) | **Pre-heat.** Low-temperature CIP stages and cheese milk heating fit fully. Precedent: Berg-Käserei Gais heats its milk with data-centre waste heat from Rechenzentrum Ostschweiz (RZO), about **1.5 GWh/a** ([RZO factsheet](https://rechenzentrum-ostschweiz.ch/wp-content/uploads/2024/10/2024_RZO_010_Factsheets_Broschuere_01_03-WEB.pdf)) | Production shifts, often 2–3 shifts, 5–6 days | Feldschlösschen supplies **12 GWh/a** of its own waste heat to Rheinfelden ([AEW](https://www.aew.ch/sites/default/files/2019-06/Waermeverbund-Rheinfelden-Mitte-Projektdatenblatt.pdf)), so it is a heat *source*, not a target | Dairy 1.5 GWh ⇒ **~170 servers** (est.) |
| **Hotels** | Hot water, space heating, kitchen, spa/pool | Hot water **60 °C at the tank, 55 °C in the loop** (BAG/BLV via [suissetec](https://suissetec.ch/files/PDFs/Ueber_uns/Deutsch/Wassertemperatur%20Trinkwasserinstallationen_Information_DE.pdf)) | Space heating: fit. Hot water: pre-heat plus booster | Morning and evening hot-water peaks; 24/7 base (BDEW GBH, Part 3) | **14–16 kWh per guest night** (eco-labelled hotel, [UNWTO/HES](https://www.untourism.int/archive/global/publication/analysis-energy-use-european-hotels-online-survey-and-desk-research)) | 100-room hotel at 70 % occupancy ≈ 0.4 GWh ⇒ **~45 servers** (est.) |
| **Hospitals** | Hot water, HVAC reheat (OR suites and isolation rooms run 24/7), sterilisation feed, kitchen, laundry | Hot water 60/55 °C (suissetec, above). Sterilisation steam is far above 60 °C | HVAC and space heating: fit. Hot water: pre-heat | **24/7, all year**, with a strong base load | German average: **25,000–29,000 kWh heat per bed per year** ([Bundestag WD](https://www.bundestag.de/resource/blob/958254/WD-5-059-23-pdf.pdf)). Swiss acute hospitals: **4–20 MWh total energy per FTE** ([ZHAW 2020](https://www.zhaw.ch/storage/lsfm/institute-zentren/iunr/oekobilanzierung/keller-2020-spitaeler-im-umwelt-benchmarking.pdf)) | **~3 servers per bed** (est.). A 700-bed hospital ⇒ ~2,000 |
| **Care homes** | Hot water (showers, laundry), space heating at a higher room temperature | Hot water 60/55 °C (suissetec) | Pre-heat plus space heating | 24/7, all year | CH 1990s: 150,000 beds used **105,000 t heating oil** ([RAVEL/BFE](https://pubdb.bfe.admin.ch/de/publication/download/2420)) ⇒ about **8 MWh/bed·a** (est.) | ~1 server per bed (est.) |

### 1.2 Named example sites (Basel region first)

| Segment | Basel region | Rest of Switzerland |
|---|---|---|
| Pharma & biotech | **Roche** Basel (R&D, HQ) and Kaiseraugst (production, packaging) ([roche.ch](https://www.roche.ch/en/sites/basel)). **Novartis Campus** St. Johann (90 GWh/a heat, PSI above). **Bachem** Bubendorf BL (peptide API). **Idorsia** and **Switzerland Innovation Park Basel Area**, Allschwil | **Lonza** Visp. **Cerbios-Pharma**, Lugano: its HVAC runs at 50–60 °C ([BFE 10198](https://pubdb.bfe.admin.ch/en/publication/download/10198)) |
| Pools & spas | **Hallenbad Allschwil** ([BFE](https://pubdb.bfe.admin.ch/de/publication/download/816)). **sole uno Rheinfelden**: its brine is *artificially heated*, with no geothermal heat ([badi-info](https://www.badi-info.ch/a/rheinfelden-sole-uno.html)). Hallenbad Rialto, Basel | **Thermalbad Zurzach** and Bad Schinznach have their own hot springs and recover heat already, so they are weaker targets ([Kanton AG](https://www.ag.ch/umwelt-aargau/pdf/UAG_So_15_35.pdf)). Uitikon ZH indoor pool has been heated by a bunker data centre since 2008: **2,800 MWh/a** waste heat ([Computerwoche](https://www.computerwoche.de/article/2690747/rechenzentrum-heizt-oeffentliches-hallenbad.html)) |
| Agriculture | Fricktal and Baselbiet farms: hay, grain and herb drying (est., no specific site checked) | **Gebr. Meier**, Hinwil ZH greenhouse on KEZO waste heat ([BFE 4800](https://pubdb.bfe.admin.ch/de/publication/download/4800)). Oftringen AG and Sant'Antonio TI greenhouses on incinerator waste heat ([SRF](https://www.srf.ch/news/schweiz/weniger-co2-dank-abwaerme-die-haelfte-der-gewaechshaeuser-koennte-klimafreundlicher-werden)). **YASAI** vertical farm, Niederhasli ZH |
| Museum & archive | **New building for Naturhistorisches Museum Basel and Staatsarchiv Basel-Stadt** in St. Johann: climate-controlled stacks, move in **April 2028**, 26 km of holdings ([bs.ch](https://www.bs.ch/medienmitteilungen/pd/2026-staatsarchiv-zieht-ins-st-johann-archivbetrieb-fuer-sechs-monate-geschlossen)). **Schaulager** Münchenstein (controlled temperature and RH, [schaulager.org](https://schaulager.org/en/schaulager/concept)). **Augusta Raurica collection centre**, Augst BL ([Klimakonzept](https://www.augustaraurica.ch/assets/content/files/06_Ueber-uns/JbAK46_Klimakonzept-des-Sammlungszentrums.pdf)) | Swiss National Museum collection centre, Affoltern a. A. (not checked) |
| Laundries | **bardusch** Basel, ex-Zentralwäscherei Basel / Zeba ([bardusch](https://www.bardusch.com/fileadmin/Switzerland/Presse/2017-Hightech-Waescherei/Bardusch_Medienmitteilung_Einweihung_Privatwaescherei.pdf)). **Rehab Basel** in-house laundry, 700 kg/day ([Prime News](https://www.rehab.ch/en/file/1329/0ac29666/20221202_Prime_News_nachhaltiger_waschen_im_rehab_basel.pdf)) | |
| Food & beverage | **Feldschlösschen** Rheinfelden (a heat source rather than a sink, see above) | **Berg-Käserei Gais AR**, heated by RZO data-centre waste heat ([RZO](https://rechenzentrum-ostschweiz.ch/wp-content/uploads/2024/10/2024_RZO_010_Factsheets_Broschuere_01_03-WEB.pdf)) |
| Hotels | Les Trois Rois; Messe-area hotels (not checked individually) | |
| Hospitals & care | **Universitätsspital Basel (USB)**, **Kantonsspital Baselland (KSBL)**, **UKBB**, Claraspital. Care homes: Bürgerspital Basel | |

---

## Part 2: Customers that need heat AND private, local compute

### 2.1 Why data has to stay on site (legal basis)

| Rule | What it says | Who it binds |
|---|---|---|
| **revDSG / nFADP** (SR 235.1), [fedlex](https://www.fedlex.admin.ch/eli/cc/2022/491/de) | Art. 5 lit. c: health, biometric and criminal-prosecution data are *particularly sensitive*. Art. 16–17: disclosure abroad only to adequate states or with safeguards. Art. 62: breach of professional secrecy is a criminal offence | Everyone. The FDPIC applied Art. 16 ff. to Suva's move to US M365 ([EDÖB letter](https://WWW.EDOEB.ADMIN.CH/dam/edoeb/de/Dokumente/datenschutz/Antwort.%20Suva,%20Luzern%2020220513.%20Risikobeurteilung%20Projekt%20Digital%20Workplace%20_M365_%20(11).pdf.download.pdf/Antwort.%20Suva,%20Luzern%2020220513.%20Risikobeurteilung%20Projekt%20Digital%20Workplace%20_M365_%20(11).pdf)) |
| **Art. 321 StGB, professional secrecy** ([fedlex](https://www.fedlex.admin.ch/eli/cc/54/757_781_799/de#art_321)) | Doctors and their auxiliaries must not disclose patient secrets. Cloud use raises a separate secrecy question on top of data protection ([Kanton ZH Innovation Sandbox](https://www.zh.ch/de/wirtschaft-arbeit/wirtschaftsstandort/innovation-sandbox/phase-ii/medizinische-dokumentation/2-datenschutz-berufsgeheimnis-und-die-cloud.html)) | Hospitals, doctors, care homes |
| **EU/PIC/S GMP Annex 11** ([EU text](https://health.ec.europa.eu/system/files/2016-11/annex11_01-2011_en_0.pdf), [PIC/S](https://picscheme.org/docview/9714)) | Data integrity (ALCOA+) for computerised GMP systems. Outsourcing needs contracts and audit rights. Commentary advises private or community cloud for sensitive data ([GMP-Compliance](https://www.gmp-compliance.org/gmp-news/ensuring-the-data-integrity-of-cloud-service-providers)). Switzerland is a PIC/S member | Pharma and biotech manufacturing and QC labs |
| **Art. 47 BankG and FINMA Circ. 2018/3** ([FINMA](https://www.finma.ch/en/news/2017/12/20171205-mm-rs-outsourcing/), [SBVg opinion](https://www.swissbanking.ch/_Resources/Persistent/b/1/3/3/b13339fe5dcd344e715dbe0a899afe3c8c56ed0b/SBVg_Bankgeheimnis_und_Cloud_Gutachten_LLAG_2019_DE.pdf)) | Bank-client secrecy. Outsourcing is allowed with controls; FINMA leaves secrecy to criminal law | Banks and insurers. Outsourcing is common: BKB outsources to Swisscom ([Swisscom](https://swisscom.ch/en/about/news/2020/07/10-kantonalbanken.html)) |
| **Cantonal data-protection laws** (e.g. IDG Basel-Stadt) and the federal cloud framework ([BK](https://www.bk.admin.ch/dam/bk/de/dokumente/dti/themen/cloud/rechtsrahmen.pdf.download.pdf/Rechtlicher%20Rahmen%20f%C3%BCr%20die%20Nutzung%20von%20Public-Cloud-Diensten%20in%20der%20Bundesverwaltung%20(inkl.%20Anh%C3%A4nge%20A%20und%20B).pdf)) | Public bodies must control where personal data is processed; foreign-law access such as the US CLOUD Act is a known risk | Cantons, cities, public hospitals, universities |
| **Bodycams in public transport** | The FDPIC ordered BLT on 29 Sep 2026 to stop bodycam processing for lack of a legal basis. BLT appealed. The Federal Council opened a consultation on 26 Aug 2026 on a law allowing bodycams for transport police and control/escort staff ([Netzwoche](https://www.netzwoche.ch/news/2026-10-07/edoeb-will-bodycam-einsatz-stoppen-doch-blt-setzt-sie-weiter-ein)) | SBB, BLT, BVB, police |

### 2.2 Segments with both needs

| Segment | Heat need | Compute need | Why it must stay local | Basel / Swiss examples |
|---|---|---|---|---|
| **Hospitals** | 24/7 hot water, HVAC reheat, all year (Part 1) | Clinical LLMs on patient records; transcription of doctor–patient talks; imaging AI (radiology, pathology) | Health data are particularly sensitive (nFADP Art. 5c); patient secrecy (StGB 321) | **USB** runs a *"high-performance GPU cluster that enables fully local processing of sensitive patient data"* and tests LLMs in oncology, dermatology, psychosomatics, pathology and radiology ([USB, 9 Dec 2024](https://www.unispital-basel.ch/en/newscenter/medienmitteilungen/09-12-2024)). **KSBL** is rolling out Ibex AI pathology ([MobiHealthNews](https://mobihealthnews.com/node/150998)) |
| **Pharma & biotech** | HVAC at 50–60 °C, 24/7; about 45 % of site heat at Cerbios (Part 1) | Molecular simulation and docking, protein models, high-content image analysis of lab and microscopy data, QC data pipelines | GMP data integrity (Annex 11), trade secrets and IP, patient data from trials | **Roche** has 3,500+ NVIDIA GPUs across on-premise (US and Europe) and cloud, including 2,176 Blackwell GPUs added in Mar 2026 ([Roche](https://www.roche.com/media/releases/med-cor-2026-03-16)). Big pharma builds its own data centres, so **mid-size firms** (Bachem, Idorsia, Switzerland Innovation Park tenants) are the realistic DigitalHeat customers (est.) |
| **Universities & research** | Lab buildings with fume hoods, 24/7 ventilation; Uni Basel heat **20.2 GWh (2019)** ([unibas](https://www.unibas.ch/de/Universitaet/Portraet/Unsere-Werte/Nachhaltigkeitsbericht-2019-2020/Energie-Ressourcen-Emissionen/Energie.html)) | HPC and GPU for life sciences; trusted research environment for clinical data | Human-research and patient data, ethics approvals | **sciCORE** (Uni Basel): 14,528 cores and 128 GPUs. **sciCORE+** is a trusted research environment for sensitive data ([sciCORE docs](https://docs.scicore.unibas.ch/HPC%20Cluster/getstarted/), [sciCORE+](https://scicore.unibas.ch/projects/scicoremed/)) |
| **Municipalities & cantons** | Public pools, schools, admin buildings, archives (Part 1) | Transcription of meetings and hearings, translation, internal chatbots, OCR of archive holdings | Cantonal data-protection law; inputs must stay under cantonal control | **Kanton Basel-Stadt**: *Transcribo* (audio→text, 96 languages), TextMate and BS-Übersetzer run on the cantonal data and AI platform, cleared up to *elevated protection need*. *BebbiBot* "runs entirely within cantonal infrastructure" ([bs.ch](https://www.bs.ch/schwerpunkte/daten/databs/schwerpunkte/kuenstliche-intelligenz/ki-nutzung-im-kanton)) |
| **Security & transport** | Depots and workshops (vehicle washing, workshop heating, staff showers): year-round hot water (est.) | Bodycam video: redaction, incident search, evidence indexing | Video of passengers is personal data; the FDPIC challenge shows how sensitive it is | **SBB transport police**: bodycams since Sep 2024, 100 cameras, 25 % fewer assaults in the first 6 months ([swissinfo](https://www.swissinfo.ch/eng/various/sbb-transport-police-officers-are-now-on-patrol-with-bodycams/87472870), [SRF](https://www.srf.ch/news/schweiz/bilanz-der-sbb-bodycams-tragen-zur-entschaerfung-von-konflikten-bei)). SBB is considering a **voluntary pilot for train attendants** ([SRF, 4 Nov 2025](https://www.srf.ch/news/schweiz/sbb-prueft-pilotprojekt-bodycams-nun-auch-fuer-zugbegleiterinnen-und-zugbegleiter)). **BLT** ticket inspectors have worn bodycams since Jan 2026 (Netzwoche above). **BVB** is tendering incident-recording software for its inspection devices ([TED](https://ted.europa.eu/de/notice/383778-2026/pdf)) |
| **Banks & insurers** | Office buildings only: weekday daytime, winter-peaked (weak) | Fraud models, document AI on client files | Bank-client secrecy (Art. 47 BankG); FINMA outsourcing rules | BKB, BLKB, Baloise/Helvetia, BIS (Basel). They already outsource to Swiss DCs, so local compute adds little (est.) |

### 2.3 Top 5 "one customer, two needs" pilot targets

| Rank | Target | One-line reason |
|---|---|---|
| 1 | **Universitätsspital Basel** | 24/7 heat all year (hot-water pre-heat, HVAC) plus a GPU cluster already running locally for LLMs on patient data under nFADP and Art. 321 StGB. Proven demand on both sides. |
| 2 | **Mid-size pharma/biotech R&D site** (Bachem Bubendorf, Idorsia or Switzerland Innovation Park, Allschwil) | Cleanroom and HVAC heat at exactly 50–60 °C, 24/7 (about 45 % of site heat at Cerbios), plus GMP- and IP-sensitive simulation and imaging compute. Too small to build its own GPU data centre. |
| 3 | **Kanton Basel-Stadt (IT BS)** | Already insists that AI inputs stay inside the canton (Transcribo, BebbiBot). Owns year-round heat sinks: pools such as Rialto, and the new archive and museum building in St. Johann opening April 2028, with climate-controlled stacks and summer dehumidification. |
| 4 | **Universität Basel / sciCORE+** | Trusted research environment for sensitive clinical data plus 24/7 lab ventilation heat (20 GWh/a university-wide). Academic partner for a measured pilot. |
| 5 | **BLT / BVB (or SBB) depot** | Bodycam video must not leave a controlled environment: the FDPIC ruling and the 2026 federal consultation make local processing a selling point. Depots have year-round wash-water and workshop heat (est.). |

Honourable mention: an **indoor pool run by a municipality** such as Allschwil or Rheinfelden. It is the best heat customer, and Deep Green has proven the model, but the compute must be sold to third parties, which is not "own data" (est.).

---

## Part 3: Typical daily heat-demand profiles

### 3.1 Source and method

**Source:** BDEW/VKU/GEODE standard load profiles for gas (SigLinDe), the hourly factors used by German gas grid operators for heat customers ([BDEW](https://www.bdew.de/energie/standardlastprofile-gas/)). Data file used: [`shlp_hour_factors.csv` in oemof demandlib](https://raw.githubusercontent.com/oemof/demandlib/master/src/demandlib/bdew/bdew_data/shlp_hour_factors.csv). Weekday levels come from [`shlp_weekday_factors.csv`](https://raw.githubusercontent.com/oemof/demandlib/master/src/demandlib/bdew/bdew_data/shlp_weekday_factors.csv).

**Profile codes:**
- GKO: public administration, banks and insurers (office-type)
- EFH / MFH: single-family house / multi-family building
- GWA: laundries
- GMK: metal and automotive (small industry)
- GBH: accommodation (hotels)
- GGB: horticulture

**What the numbers measure:** gas consumed at the meter, including hot water. They therefore show thermostat setback and the morning boost.

**How we processed them:** each day's 24 values were normalised to a mean of 1.0. The temperature class is the daily mean outdoor temperature:
- 6–10 °C: a typical Basel Nov/Mar day
- −4 to 0 °C: a cold winter day
- 16–20 °C: a summer day, mostly hot water

The climate is comparable to Basel, which sits on the German border.

**Caveats:** shapes are within-day only. Weekday-to-weekend levels are listed further down. Read the factors as **heat delivered by the boiler**. This is not occupancy.

### 3.2 Hourly shape factors (24 values, mean = 1)

| Hour | (a) Office GKO Mon–Fri, 6–10 °C | Office GKO Sun, 6–10 °C | Office GKO Mon–Fri, −4–0 °C | (b) House EFH, 6–10 °C | House EFH, 16–20 °C (mostly hot water) | Flats MFH, 6–10 °C | (c) Laundry GWA Mon–Fri, 6–10 °C | (c) Metal/auto GMK Mon–Fri, 6–10 °C | Hotel GBH Mon–Fri, 6–10 °C |
|---|---|---|---|---|---|---|---|---|---|
| 00-01 | 0.70 | 0.69 | 0.83 | 0.47 | 0.24 | 0.55 | 0.13 | 0.80 | 0.74 |
| 01-02 | 0.76 | 0.84 | 0.84 | 0.49 | 0.24 | 0.61 | 0.12 | 0.82 | 0.78 |
| 02-03 | 0.76 | 0.77 | 0.82 | 0.51 | 0.26 | 0.57 | 0.12 | 0.84 | 0.74 |
| 03-04 | 0.87 | 1.17 | 0.94 | 0.59 | 0.38 | 0.61 | 0.12 | 0.85 | 0.90 |
| 04-05 | 1.11 | 1.52 | 1.04 | 0.80 | 0.72 | 0.83 | 0.25 | 0.87 | 1.08 |
| 05-06 | 1.20 | 1.72 | 1.07 | 1.18 | 1.63 | 1.24 | 0.60 | 0.93 | 1.10 |
| 06-07 | **1.49** | 1.15 | 1.24 | **1.49** | **2.05** | 1.26 | 1.09 | 1.18 | 1.29 |
| 07-08 | 1.47 | 1.15 | **1.30** | 1.38 | 1.77 | 1.21 | 1.65 | 1.57 | **1.35** |
| 08-09 | 1.41 | 1.07 | 1.28 | 1.26 | 1.45 | 1.18 | 1.84 | **1.58** | 1.19 |
| 09-10 | 1.28 | 1.05 | 1.20 | 1.16 | 1.44 | 1.11 | 1.95 | 1.45 | 1.08 |
| 10-11 | 1.19 | 0.99 | 1.14 | 1.08 | 1.19 | 1.07 | 1.76 | 1.31 | 1.02 |
| 11-12 | 1.12 | 0.97 | 1.09 | 1.04 | 1.15 | 1.04 | **1.99** | 1.14 | 0.96 |
| 12-13 | 1.06 | 0.91 | 1.07 | 1.02 | 1.06 | 1.02 | 1.74 | 1.05 | 0.92 |
| 13-14 | 1.03 | 0.92 | 1.03 | 1.02 | 0.94 | 1.00 | 1.75 | 0.97 | 0.90 |
| 14-15 | 1.01 | 0.92 | 1.00 | 1.05 | 0.89 | 1.00 | 1.38 | 1.02 | 0.89 |
| 15-16 | 0.97 | 0.89 | 1.01 | 1.10 | 0.85 | 1.03 | 1.55 | 0.96 | 0.91 |
| 16-17 | 0.92 | 0.92 | 0.96 | 1.16 | 0.95 | 1.09 | 1.38 | 0.95 | 0.95 |
| 17-18 | 0.93 | 1.06 | 0.97 | 1.23 | 1.01 | 1.15 | 1.35 | 0.84 | 1.04 |
| 18-19 | 0.89 | 0.96 | 0.95 | 1.26 | 1.12 | 1.20 | 0.70 | 0.78 | 1.10 |
| 19-20 | 0.86 | 0.92 | 0.93 | **1.26** | 1.25 | **1.23** | 0.71 | 0.82 | 1.14 |
| 20-21 | 0.84 | 0.98 | 0.90 | 1.20 | **1.26** | 1.22 | 0.63 | 0.83 | 1.14 |
| 21-22 | 0.77 | 0.84 | 0.83 | 1.03 | 1.06 | 1.11 | 0.61 | 0.83 | 1.07 |
| 22-23 | 0.67 | 0.76 | 0.77 | 0.69 | 0.72 | 0.95 | 0.43 | 0.77 | 0.90 |
| 23-24 | 0.69 | 0.81 | 0.79 | 0.52 | 0.37 | 0.71 | 0.13 | 0.80 | 0.81 |
| max/min | 2.2 | 2.5 | 1.7 | 3.2 | 8.6 | 2.3 | 16.9 | 2.0 | 1.8 |

**Weekday level factors, Mon→Sun** (multiply the daily total):

| Profile | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| GKO (office) | 1.035 | 1.052 | 1.045 | 1.049 | 0.988 | 0.886 | 0.944 |
| GWA (laundry) | 1.246 | 1.261 | 1.271 | 1.243 | 1.128 | 0.388 | 0.462 |
| GMK (metal/auto) | 1.070 | 1.037 | 0.993 | 0.995 | 1.066 | 0.936 | 0.903 |
| GBH (hotel) | 0.977 | 1.039 | 1.003 | 1.016 | 1.002 | 1.004 | 0.958 |
| EFH, MFH (homes) | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### 3.3 What the shapes mean for DigitalHeat

**(a) Office:**
- Night setback runs 22–03 at about 0.7.
- The **morning boost peaks at 06–08 (about 1.5)**, then decays through the working day to about 0.9 by 17–18.
- On cold days the curve flattens (max/min 1.7), because the building has to be held warm.
- On Sundays the boost comes early (04–06), then the building stays near flat.

The SIA 2024 office occupancy profile (about 07–18 on weekdays) is consistent with this. SIA 2024 itself is paywalled; the HSLU thesis notes it uses daily person profiles ([HSLU thesis](https://sites.hslu.ch/ta-bachelorarbeiten/wp-content/uploads/sites/6/2023/06/BAT_G_23_12_Merdanovic_Mostefai.pdf)).

**(b) Residential:**
- **There are two peaks: 06–07 (1.5) and 18–21 (1.26).** The night trough is about 0.5.
- On summer days (hot water only) the morning spike is 2.05 and the night trough is 0.24.

VDI 4655:2021 gives reference profiles for type days at 1-minute and 15-minute resolution. It is paywalled ([DIN Media](https://www.dinmedia.de/de/technische-regel/vdi-4655/336886496)), so we used BDEW.

**(c) Process / industrial:**
- Laundry (GWA) is a **single day shift, 06–18**, at up to 2.0, with almost zero at night. The 30-minute buffer tank cannot bridge that, so the scheduler should shift compute into 06–18.
- Metal and automotive (GMK) is flatter: max/min 2.0, peak at 07–09.
- A **3-shift pharma or cleanroom HVAC load is close to flat** (est. about 1.0 ± 0.15). BDEW has no 3-shift profile. The demandlib industrial step profile defaults to day 0.8 / night 0.6 on weekdays, with the day running 07:00–23:30 ([demandlib](https://github.com/oemof/demandlib/blob/master/src/demandlib/particular_profiles.py)). For measured US manufacturing shapes by shift structure, see [NREL / OpenEI](https://data.openei.org/submissions/8683).

**Horticulture (GGB):** night-heavy. About 1.4–1.7 at 22–08 and about 0.3 at 11–15 (6–10 °C class; same data file). This is the opposite of offices.

### 3.4 Specific heat demand of Swiss office buildings

| Stock | Value | Source |
|---|---|---|
| Existing offices (fuel demand) | **430–1,000 MJ/m²·a = 120–280 kWh/m²·a**, some above 1,500 MJ (above 415 kWh) | BFE 2006, Jakob et al. (ETHZ / Amstein+Walthert / HTA Luzern; co-funded by Basel), [newsd 4717](https://www.newsd.admin.ch/newsd/message/attachments/4717.pdf) |
| New offices, 2006 practice | 140–280 MJ/m²·a = **39–78 kWh/m²·a**; can be cut to 90–140 MJ (25–39 kWh) | same |
| New offices, current legal limit (SIA 380/1:2016 via MuKEn; BE text) | Category III, administration: Q_H,li = **13 + 15 × (A_th/A_E) kWh/m²·a** at 9.4 °C annual mean (−6 % per K warmer). Renovations: 1.5 × the new-build limit | [BELEX BE annex 741.111](https://www.belex.sites.be.ch/api/de/versions/2795/annexes) |
| ⇒ typical new office, form factor A_th/A_E 1.0–1.5 | **about 28–35 kWh/m²·a** space heat; **about 25–33** at Basel's warmer climate | (est.) from the formula above |
| Minergie-P office, measured | 13.9 kWh/m²·a (climate-corrected), Winterthur | [BFE](https://pubdb.bfe.admin.ch/de/publication/download/10054) |

**Implication:** a 1,000 m² new office needs only about 30 MWh/a, about 3–4 servers, and almost nothing in summer. Old stock needs 4–9× more but is just as seasonal. **Offices are a winter-only customer** (est.).

### 3.5 Hot water for a 4–5 person household

| Item | Value | Source |
|---|---|---|
| Planning demand at 60 °C (cold water 10 °C) | **40 / 45 / 55 L per person per day** (simple / medium / high) | SIA 385/2:2015 via [HSLU](https://hslu-ige-laes.github.io/lcm/docs/modules/flatHotWater/interpretation) |
| 4–5 persons, medium | **180–225 L/day at 60 °C** | (est.) |
| Useful energy (ΔT 50 K, 0.058 kWh per litre) | **about 10.5–13 kWh/day** (simple: 9.3–11.6; high: 12.8–16), about 3.8–4.8 MWh/a | (est.) |
| With storage and circulation losses (+20–40 %) | **about 13–18 kWh/day** | (est.) |

**Pitch line:** one 1 kW server gives off **24 kWh/day**. That is more than the year-round hot water of a 4–5 person household, which is why hot water is the summer base load for homes (est.). The catch is temperature: legionella rules need 60 °C at the tank ([suissetec](https://suissetec.ch/files/PDFs/Ueber_uns/Deutsch/Wassertemperatur%20Trinkwasserinstallationen_Information_DE.pdf)), so 50–60 °C server water needs a small top-up or periodic disinfection.

---

## Part 4: Resilience evidence (cloud and IT outages)

| Date | Event | Scope | Source |
|---|---|---|---|
| 19 Jul 2024 | CrowdStrike Falcon content update crashes Windows | **About 8.5 million Windows devices** worldwide (airlines, hospitals, banks); "less than one percent of all Windows machines" | [Microsoft blog, 20 Jul 2024](https://blogs.microsoft.com/blog/2024/07/20/helping-our-customers-through-the-crowdstrike-outage/) |
| 19–20 Oct 2025 | AWS us-east-1: a race condition in DynamoDB's DNS automation leaves an empty DNS record, which cascades to EC2 and NLB | 23:48 PDT 19 Oct to 14:20 PDT 20 Oct (**about 14.5 h**); thousands of apps worldwide | [AWS post-event summary](https://aws.amazon.com/message/101925), [ThousandEyes](https://www.thousandeyes.com/blog/aws-outage-analysis-october-20-2025) |
| 29–30 Oct 2025 | Azure Front Door: an inadvertent tenant configuration change stops AFD nodes loading | 15:45 UTC 29 Oct to 00:05 UTC 30 Oct (**about 8 h**); Microsoft 365, Azure portal and customer sites. It was the second AFD incident that month (9 Oct) | [Azure status history, ID YKYN-BWZ](https://azure.status.microsoft/en-us/status/history/), [Microsoft Azure Networking blog](https://techcommunity.microsoft.com/blog/azurenetworkingblog/-/4479416), [ThousandEyes](https://www.thousandeyes.com/blog/microsoft-azure-front-door-outage-analysis-october-29-2025) |

**Pitch angle:** each of these outages started at a single central point (a config push, a DNS record, one region). Compute spread across building basements, with local fallback, does not share that single point of failure (est.).

---

## Gaps and caveats

- No Swiss source found for pharma CIP setpoints, brewery mash temperatures, or hotel hot-water shares. These cells use international sources or are marked (est.).
- The Novartis 90 GWh/a figure is from 2003 (PSI); the campus has changed since.
- The USB bed count was not checked, so the "~2,000 servers" figure is illustrative.
- BDEW profiles are German gas-meter data. The office and home shapes carry over well to Basel; process profiles vary a lot by site.
- SIA 385/2 has a 2025 edition (SN 546385/2:2025); the litre values above are from the 2015 edition.

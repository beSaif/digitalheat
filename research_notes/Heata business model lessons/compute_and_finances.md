# Heata (heata.co): compute customers, revenue model, funding, scale and corporate status

Research date: 2026-11-21. Every claim carries the date of its source. "Stale" means the source is more than about 12 months old and nothing newer was found.

**Important entity note.** Heata trades through **BIT WARMER LIMITED, company no. 11110428**. The SLA and customer agreement both say: "Bit Warmer Limited (trading as 'heata'). Registered office: Wood Farm, Portsmouth Road, Godalming, England, GU7 2JR. Company Number: 11110428. VAT number: 294 2496 68." — [heata Standard SLA 2026 PDF](https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf); [heata customer agreement PDF](https://docs.heata.co/downloads/heata%20customer%20agreement_compute%20services.pdf).
A Companies House search for "HEATA LIMITED" returns company **13140425**. That company is **unrelated**: it was formerly "ECO BY ASSURE LIMITED" (renamed 17 Feb 2025), is based in Blackburn, has SIC 41202 (construction of domestic buildings) and has the Rawnsley family as directors — [Companies House 13140425](https://find-and-update.company-information.service.gov.uk/company/13140425). Do not use its filings.

---

## 1. Compute customers: who buys, what workloads, scheduling, interruption, security, SLA

### Takeaway
Heata sells batch and stateless compute, mainly CPU, plus RTX 4090 GPUs. It began with 3D rendering for architecture and animation studios (2022–2024). It later moved to generic cloud services: Kubernetes, spot-like VMs, GitHub Actions runners, Ray via Anyscale, Kubeflow and Bacalhau. The only enterprise customer it names is Centrica/British Gas. Its customer list is short and made up mostly of pilots. Customers control their workloads from cloud-hosted access nodes on GCP. The in-home workers are disposable, and Heata can "cloud burst" to public cloud to meet its SLA. This means the capacity guarantee is partly backed by hyperscaler capacity, not by homes alone.

### Cited Findings
**Named customers and logos**
- Centrica is the headline customer. Quote on the compute page (live Nov 2026): "Running our workloads on the heata network has demonstrated that we can provide significant benefits to both Centrica and households." — Peter Simons, Head of Cloud Architecture, Centrica — [heata.co/compute](https://www.heata.co/compute)
- The "TRUSTED BY" logo strip on the compute page shows exactly two logos: **Centrica** and **DEFRA** (alt text "Centrica logo", "DEFRA logo"). Microsoft for Startups and Google for Startups appear separately under "SUPPORTED BY" — [heata.co/compute](https://www.heata.co/compute) (page HTML, retrieved 2026-11-21). No public detail on DEFRA's usage was found (see Gaps).
- British Gas trial, 5 Feb 2025: "As part of a three-month trial, 10 heata units will be installed in the homes of British Gas employees, and the energy provider's computing workloads will be processed on these units." It "will … further co-develop customer propositions in 2025." — [Centrica press release, 5 Feb 2025](https://www.centrica.com/media-centre/news/2025/british-gas-partners-with-heata-on-trial-to-reuse-waste-heat-from-data-processing/); [heata blog copy](https://www.heata.co/content-hub/british-gas-partners-with-heata-to-launch-innovative-trial-to-reuse-waste-heat-from-data-processing-and-save-households-money). Stale (Feb 2025). No follow-up results were published.
- 3D rendering customers named on the Media Cymru render page (live Oct 2026): **F10 Studios** (Nick Homer, MD), **Eleven Visualisation** (rendered "a 40-second passion piece … premiered at D2 Conference"), and **Model Works** for client **Landsec** — [heata.co/render/mediacymru](https://www.heata.co/render/mediacymru)
- Sept 2023: "Our main focus right now is expanding our base of 3D rendering customers such as animation and visualisation studios - We recently rendered a 2 minute flythrough for Landsec and Model Works which saved 250kg of carbon and generated 14 tonnes of hot water." — Michael Paisley, co-founder/CCO — [heata seed announcement, 26 Sep 2023](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding). Stale.
- Same post: "our cloud customers - which include companies with heavy cloud compute requirements such as 3D animation and visualisation studios" — [same](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding)
- **Equal Experts**, a software consultancy, is a channel partner and probably also a user (Oct 2024): "Partnering with Heata is not only enabling us to reduce the carbon footprint of our cloud activities … We're excited to bring this opportunity to our client base" — Lewis Crawford, Equal Experts — [heata x Expanso announcement, 1/28 Oct 2024](https://www.heata.co/compute/heata-and-expanso-team-up-to-expand-green-cloud-to-traditional-workloads)
- **Civo** was a channel and pilot partner (Jan 2023): "Civo customers being given the option to trial running cloud workloads on the Heata network." Civo CEO Mark Boost later led the seed round — [DCD, 9 Jan 2023](https://www.datacenterdynamics.com/en/news/civo-partners-with-heata-to-offer-batch-processing-on-digitized-boilers/) (read via Wayback). Stale.
- **UK government pilot**: on 9 Oct 2026 heata was announced as one of two winners of "Pitch in Whitehall: Green Compute", run by Startup Coalition with the Government Digital Service. GoCodeGreen was the other winner. "The win comes with a pilot contract with government. We'll share more as the pilot takes shape." — [heata blog, 9 Oct 2026](https://www.heata.co/content-hub/heata-wins-pitch-in-whitehall-green-compute). Only heata's own post confirms this; no contract value is given.
- **South of Scotland Enterprise** (Oct 2024): "SOSE is excited to be supporting the expansion of the heata network in Scotland … we want local businesses to run workloads on green data assets such as the heata network" — Tom Bishop, SOSE — [heata x Expanso post](https://www.heata.co/compute/heata-and-expanso-team-up-to-expand-green-cloud-to-traditional-workloads). The form of support (grant or other) was not stated.
- Microsoft's MAIDAP graduate team ran a carbon-aware scheduling hackathon on a *simulated* 10,000-node heata network (Feb 2024). This was a collaboration, not paid usage — [heata blog, 23 Feb 2024](https://www.heata.co/content-hub/data-centre-carbon-hackathon-microsoft-azure-centralised-vs-heata-distributed)

**Workloads and products**
- Current positioning (Nov 2026): "Move stateless, parallel workloads such as containers, AI inference, batch processing, CI/CD pipelines and ML training onto heata, and keep data centre capacity for what needs it." The FAQ lists: "high-volume repetitive jobs, machine learning training and inference, CI pipelines, research and data processing, computational finance and risk analysis, and climate modelling. Work that needs one very large machine, or very low latency to a single place, is a poorer fit." — [heata.co/compute](https://www.heata.co/compute)
- Services menu (Nov 2026): Kubernetes (dedicated K3s cluster per client), VM Clusters ("disposable Ubuntu VMs with full root"), GitHub Action Runners, Ray via Anyscale ("Heata appears as an available cloud in your Anyscale account"), Kubeflow/Jupyter notebooks, ECS Anywhere/Azure Arc hybrid — [heata.co/compute](https://www.heata.co/compute); [docs.heata.co/services/anyscale](https://docs.heata.co/services/anyscale/)
- Ray beta (4 Jul 2025): "Beta workloads include batch jobs, ML tasks, Python tasks … your job could be running across dozens of airing cupboards." — [heata blog](https://www.heata.co/content-hub/from-ray-workloads-to-hot-water-the-heata-model-in-action)
- Bacalhau/Expanso integration (Oct 2024) lets "Docker and WASM workloads … run in a distributed way across the Heata network" — [heata x Expanso](https://www.heata.co/compute/heata-and-expanso-team-up-to-expand-green-cloud-to-traditional-workloads)
- Example work types listed on the 2024 compute page: "Computational Fluid Dynamics, Finite Element Analysis, Climate modelling, Computational finance and risk analysis, Higher education research, In silico drug research" — [heata.co/compute, Wayback 23 Jun 2024](https://web.archive.org/web/20240623112054/https://www.heata.co/compute)
- GPU hardware: "Every node is a GeForce RTX 4090 — 24GB … Board power 450W per card". This is for the Media Cymru render farm, which sits in Y Bank, a community building in Caerphilly, not in homes. Supported renderers: V-Ray, Corona, Arnold, Cycles, Redshift — [heata.co/render/mediacymru](https://www.heata.co/render/mediacymru)
- Node spec (2024): "How powerful is a node? Default deployment is on: 54 vCPUs, 120GB RAM, 200GB SSD scratch space." — [Wayback 23 Jun 2024](https://web.archive.org/web/20240623112054/https://www.heata.co/compute)
- Original product (2020 Innovate UK study): "Bit Warmer's 'Hot Patch' unit … performs remote compute tasks (e.g. video rendering)" — [GtR project 105712](https://gtr.ukri.org/projects?ref=105712)
- Origin: the founders started with Bitcoin mining ("we put a miner in a barrel of mineral oil and connected it up to a radiator"). They then "switched from Bitcoin mining to general compute", and moved from radiators to hot-water cylinders — [heata.co/about-us](https://www.heata.co/about-us)

**Scheduling and interruption handling**
- Architecture (docs, 2026): "Clients connect to Heata via cloud-hosted access nodes. These are always on and are where control planes and orchestration live … Heata worker nodes are ephemeral … no single worker is critical. If a worker goes offline, workloads redistribute across the fleet automatically." — [docs.heata.co](https://docs.heata.co/)
- "Access Nodes are hosted within GCP" — [heata SLA, Aug 2026](https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf)
- Cloud burst (SLA, Aug 2026): "Where necessary the Heata Network can also call upon Cloud Burst Nodes to manage peaks in demand and to guarantee service." Also: "To guarantee delivery of workloads we may use cloud instances (Cloud Burst Nodes) in addition to our distributed Worker Nodes. This will be recorded and we can provide you with this information." Cloud Burst is defined as using cloud capacity "to guarantee delivery of workloads to meet the SLA or to deal with overcapacity on the network." — [SLA PDF](https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf)
- Heata can use clients' idle capacity to keep tanks warm: "In situations where a Client has Allocated Capacity but is not actively using it, Heata reserves the right to utilise this capacity to maintain efficient utilisation of the network and ensure reasonable hot water delivery to the household(s) … fully sandboxed … if the Client submits workloads, these will take priority." — [SLA PDF](https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf)
- When the tank is full: "In practice the utilisation level will be lower and sometimes the water will be at temperature so the heata unit won't be able to run." — [heata.co/free-hot-water FAQ](https://www.heata.co/free-hot-water)
- Ray's role (Jul 2025): "If a device drops out (say, due to a network issue), Ray automatically reroutes tasks. It checkpoints jobs, retries tasks". Combined with heata's own health checks — [heata Ray post](https://www.heata.co/content-hub/from-ray-workloads-to-hot-water-the-heata-model-in-action)
- 2024 model: "Heata Compute Nodes are then treated like spot instances, as one may occasionally be replaced by another. But unlike spot we guarantee your chosen number of nodes to be online during the deployment – we guarantee throughput." — [Wayback Jun 2024](https://web.archive.org/web/20240623112054/https://www.heata.co/compute)
- Hackathon design constraint (Feb 2024): "As heata network provides heat to homes, we needed to maintain a minimum utilisation of >50% on each node in any given month (and all nodes must be used)." — [heata blog](https://www.heata.co/content-hub/data-centre-carbon-hackathon-microsoft-azure-centralised-vs-heata-distributed)
- Spot VMs (docs 2026): "Ideal for fault-tolerant workloads … where interruptions can be handled gracefully." Flavours: standard 2 vCPU/4 GiB, compute 4/8, memory 8/16 — [docs.heata.co/services/spot-vms](https://docs.heata.co/services/spot-vms/)

**Security and confidentiality**
- "Each client's workloads run in isolated, encrypted virtual machines on private VPN networks, backed by Cyber Essentials Plus certification and independent penetration testing." — [heata.co/compute](https://www.heata.co/compute)
- Controls: LUKS2 AES-256-XTS with TPM-sealed keys; WireGuard; "USB fingerprinting and chassis intrusion, which disconnects a compromised unit"; public-key SSH plus 2FA. "On the roadmap: ISO 27001, AMD SEV confidential computing, container image signing and SBOMs". The full policy is available "under NDA on request" — [heata.co/compute/security](https://www.heata.co/compute/security)
- Platform: "SUSE Micro OS with read-only root filesystem … UEFI Secure Boot with Heata-signed kernels only … Lynis security auditing — 300+ security tests on every reboot" — [docs.heata.co/security](https://docs.heata.co/security/)
- "Compute loads are on a Private Subnet, isolated from the home network … Compute jobs are unable to access the host's wifi". Single tenancy is available on request — [heata.co/compute FAQ](https://www.heata.co/compute)
- Each unit has its own internet connection, not the host's broadband: "either their own dedicated fiber line or connection via 4G/5G" — [DCD, Jan 2023](https://www.datacenterdynamics.com/en/news/civo-partners-with-heata-to-offer-batch-processing-on-digitized-boilers/). The 2026 landlord page asks for "Broadband at the property, or somewhere we can add a 4G router" — [heata.co/landlords-sign-up](https://www.heata.co/landlords-sign-up). This may mean they now use the property's broadband; it is unclear.
- "Customer data continues living in your primary cloud platform" (the data stays in the customer's cloud) — [heata.co/compute](https://www.heata.co/compute)

**SLA (Standard SLA, "Last Updated: August 2026")**
- "Access Nodes have a monthly Uptime of >99.5%. Worker Nodes have a Committed Capacity of >99.5%". The service-credit table pays 10% if Access Node uptime is < 99.9%, 25% if < 95.0% and 100% if < 90.0%. For committed capacity it pays 10% if < 99.5%, 25% if < 95% and 100% if < 90%. Credits are capped at 50% of the monthly bill and expire after 12 months — [SLA PDF](https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf). **Internal inconsistency:** the PDF text says >99.5% uptime but the credits trigger below 99.9%. The website FAQ says "Better than 99.9% monthly uptime on the cloud access node … and better than 99.5% committed capacity per job cluster … Spot capacity is priced lower and carries no SLA" — [heata.co/compute](https://www.heata.co/compute)
- Support tiers: Standard (included, P1 response 8h); Priority (5% of spend, min £500; P1 2h); Enterprise (10% of spend, min £1,000; P1 30 min, 24/7) — [docs.heata.co/pricing-billing](https://docs.heata.co/pricing-billing/); [SLA PDF](https://docs.heata.co/downloads/heata%20_Standard%20SLA_2026.pdf)

### Inferences
- The customer base looks very small. Only Centrica is named as an enterprise compute customer, and that was a 10-unit employee trial. The other named users are small studios doing one-off renders and pilot or channel partners (Civo, Equal Experts, Anyscale/Expanso integrations). DEFRA appears only as a logo.
- The product has moved twice: from Bitcoin mining to 3D rendering (2022–24), then to generic Kubernetes/VM/CI/Ray (2024–26). This looks like a search for a workload with enough steady demand to keep tanks hot.
- Cloud-burst fallback, GCP-hosted control planes and the right to run filler jobs on idle client capacity together show the core tension. Heat delivery needs steady utilisation, while SLA delivery needs spare capacity. Heata covers the SLA side partly with hyperscaler capacity.

### Gaps
- No customer count, revenue by customer, or named customer beyond Centrica on the compute side. What DEFRA uses was not found.
- No public description of the scheduler logic, such as how it reads tank temperature or thermostat state, or a priority queue for "filler" jobs. Only the outcome is described ("won't be able to run").
- No results were published from the British Gas trial (Feb 2025), and there was no announced commercial roll-out to British Gas customers.
- The value and scope of the Pitch in Whitehall pilot contract (Oct 2026) were not disclosed.

---

## 2. Pricing to customers and cost and carbon claims

### Takeaway
Since 2026 Heata publishes per-resource cloud-style prices: £0.017 per vCPU-hour managed, £0.010 spot, +£0.89 per GPU-hour for an RTX 4090, and £20 per TB egress. Reserved terms take 30% off for one year and 55% for three. Its marketing claims it is "up to 50% cheaper than the hyperscalers" and "up to 80% lower carbon". Before 2025 it priced by node-hour (£0.75 pay-as-you-go, down to £210 per node per month all-you-can-eat). Its carbon claims rest on its own location-based model (750 kg CO2e per unit per year, down from 1 t claimed in 2023), with no third-party verification found.

### Cited Findings
**Current price list (2026)**
- Managed compute: "Base vCPU … £0.017 (1.70p) / core hour; RAM … £0.0025 / GB hour; Ephemeral storage £0.00008 / GB hour." Spot: "£0.010 (1.00p)" per core-hour, "£0.0018" per GB-hour of RAM, "No SLA" — [docs.heata.co/pricing-billing](https://docs.heata.co/pricing-billing/); [heata.co/compute/kubernetes](https://www.heata.co/compute/kubernetes); [heata.co/compute/vm-clusters](https://www.heata.co/compute/vm-clusters)
- GPUs: "Tier 1: Entry 16GB - 24GB NVIDIA RTX 4090, RTX 5080, RTX A5000 … GPU-Hour from + £0.89 / hour; Tier 2: Mid 24GB - 40GB NVIDIA RTX 5090, A100 (40GB), RTX 6000 Ada … from + £1.19 / hour" — [docs.heata.co/pricing-billing](https://docs.heata.co/pricing-billing/)
- Platform fee for "Data Science" (notebooks, Ray, Spark): "0.71p per CPU hour + 0.09p per GB RAM hour + 24.73p per GPU hour". The standard CLI and Kubernetes tier is free — [same](https://docs.heata.co/pricing-billing/)
- Media Cymru render farm rate: "£2 per GPU-hour", a discounted rate for Cardiff Capital Region studios — [heata.co/render/mediacymru](https://www.heata.co/render/mediacymru)
- GitHub Actions runners: slim (1 vCPU/5 GB) £0.0011/min; standard (2 vCPU/8 GB) £0.0034/min; large (8 vCPU/32 GB) £0.0120/min, each "~25%" below GitHub's private-repo per-minute rates — [heata.co/compute/action-runners](https://www.heata.co/compute/action-runners)
- Reserved: "1-Year Reserved 30% Off; 3-Year Reserved 55% Off" (base compute only). Egress costs £20/TB after 100 GB free per month. Persistent storage costs £0.06 per GB-month. Prices exclude VAT and are billed monthly in arrears — [docs.heata.co/pricing-billing](https://docs.heata.co/pricing-billing/)
- Marketing: "Up to 50% cheaper than the hyperscalers. Flexible pricing, from as little as 1p per core hour." Rationale: "There's no land, planning or construction, no new grid connection, no electrical or power systems, and no cooling systems or cooling energy." — [heata.co/compute](https://www.heata.co/compute)

**Earlier pricing (2024 to at least mid-2025)**
- "Pay as you go … Node hour cost £0.75 … Nodes Up to 20 … Queueing possible … Cost per node per month utilised £547.50". "Medium plan … Node hour cost £0.55, Reservation fee per hour £0.03 (£25 per month) … Up to 50 … Guaranteed … £426.85 per node per month". "Heavy plan … Node hour cost Zero, Reservation fee per hour £0.29 (£210 per month) … £210 per node per month". "There are no hidden costs for VM images, other storage, or data ingress or egress." — [heata.co/compute, Wayback 23 Jun 2024](https://web.archive.org/web/20240623112054/https://www.heata.co/compute) (the same table appears in the Jul 2025 snapshot)

**Carbon and energy claims (own figures, not independently verified)**
- Current: "Around 750kg of CO2e a year per unit, compared with running the same compute in a conventional data centre and heating the same water separately." — [heata.co/compute FAQ](https://www.heata.co/compute)
- Method footnote: "Typical Data Centre + domestic hot water: 750W/hour (330W compute + 200W cooling + 220W hot water) vs heata: 330W/hour (330W compute, including 220W harnessed from waste heat), at 80% utilisation across the year. Carbon intensity is 0.274kg CO₂e/kWh … derived from the blend of heating sources in the homes in the heata network." — [heata.co/free-hot-water/heata-unit](https://www.heata.co/free-hot-water/heata-unit)
- "Ultra low carbon - up to 80% lower carbon than a typical data centre" — [heata.co home](https://www.heata.co/). "This results in a net reduction in energy use (at a system level) of 80% - delivering a carbon saving of 1 tonne per home per year" — [Ray post, Jul 2025](https://www.heata.co/content-hub/from-ray-workloads-to-hot-water-the-heata-model-in-action)
- Earlier claims (2023): "Each heata unit uses 56% less electricity and saves 1 tonne of carbon per year"; "we think we can get close to a PUE of 0.3"; "The heata unit transfers around 80% of the energy consumed to the tank" — [heata.co/compute, Wayback 2023](https://web.archive.org/web/20230701000000*/heata.co/compute). The seed post (Sep 2023) says "reducing energy consumption by 60%" — [heata seed post](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding)
- Hyperscaler critique: "Hyperscalers also use market-based reporting to massively under-report their carbon impact." — [heata.co/compute](https://www.heata.co/compute)
- An embeddable "Heata Impact Ticker" widget lets customers display their impact — [docs.heata.co/ticker](https://docs.heata.co/ticker/)

### Inferences
- At list price, one vCPU used for a full year on managed compute earns about £149 (£0.017 × 8,760 h), or about £88 on spot, before RAM.
- On the 2024 spec of about 54 vCPU and 120 GB per node, a fully sold node would earn about (54 × 0.017 + 120 × 0.0025) × 8,760 ≈ £10.7k a year on managed compute, or about £6.6k on spot. At 50% sold utilisation the managed figure is about £5.4k. This is an upper bound. Real realised prices are unknown, and the 2024 "Heavy" plan valued a node at only £210 a month (£2,520 a year).
- The price drop from £547.50 per node-month (PAYG 2024) to roughly 1–1.7p per core-hour suggests price-led customer acquisition.
- The carbon saving fell over time: 1 t (2023) to 750 kg (2025–26). The method assumes 80% utilisation and counts avoided cooling and avoided water heating. Real fleet utilisation appears to be lower (see §3).

### Gaps
- No published comparison against specific AWS, Azure or GCP instance prices. The "up to 50% cheaper" claim is unsupported by a worked example.
- No third-party audit of the carbon claims was found. No GHG Protocol scope treatment was stated for customers, for example whether the avoided boiler gas is claimed as a customer benefit.

---

## 3. Revenue model and unit economics

### Takeaway
Revenue comes from compute customers. Heata pays each host for the unit's electricity through a credit to their energy or bank account, metered by an accredited submeter. Hosts pay nothing and get "free" hot water. Grants are a large share of funding: about £792k from UKRI over 2020–2026, close to the roughly £1.75m raised in equity. Filed accounts suggest commercial revenue is tiny. Trade debtors were only £6,718 at end-2024 and £340 at end-2025. The company does not capitalise the in-home servers: its fixed assets total £1,989.

### Cited Findings
**Who pays for electricity (exact quotes)**
- "heata pays for the electricity used by the heata unit. Depending on your supplier, we'll either directly credit your energy account, or your bank account. An accredited billing submeter with a readable screen is included as part of the installation, which we will read remotely to get the details for your credit amounts." — [heata.co/free-hot-water FAQ](https://www.heata.co/free-hot-water) (live Nov 2026)
- "heata pays for the electricity the heata unit uses, which means the household pays less to heat their hot water." — [Centrica release, 5 Feb 2025](https://www.centrica.com/media-centre/news/2025/british-gas-partners-with-heata-on-trial-to-reuse-waste-heat-from-data-processing/)
- "A billing accredited submeter is installed along with the heata unit and the household is credited for the amount of energy that the heata unit uses." Savings are modelled "based on hot water heated with electricity at 22p/kWh, or heated with gas at 7.8p/kWh … with the heata unit supplying 4.25kWh of hot water per day" — [heata.co/free-hot-water/heata-unit](https://www.heata.co/free-hot-water/heata-unit)

**Household-side value (what heata gives away)**
- "Save £150–350 a year on your energy bill" (Nov 2026) — [heata.co/free-hot-water](https://www.heata.co/free-hot-water). British Gas trial: "up to £340 per year when offsetting electrically heated hot water, and up to £120 when offsetting gas" — [Centrica, Feb 2025](https://www.centrica.com/media-centre/news/2025/british-gas-partners-with-heata-on-trial-to-reuse-waste-heat-from-data-processing/). In 2023: "saving families up to £450 per year" — [seed post](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding); "average of £250 per year" — [MIT Technology Review, 18 Aug 2023](https://www.technologyreview.com/2023/08/18/1077548/computer-waste-heat/)
- "If the heata unit ran all day it would deliver about 4.8kWh of hot water … We think it could deliver up to 80% of an average household's hot water, with good compute utilisation." — [heata.co/free-hot-water](https://www.heata.co/free-hot-water)
- Installation "within a day", "no plumbing required", vented cylinders only ("a version for unvented cylinders is in development") — [heata.co/free-hot-water/heata-unit](https://www.heata.co/free-hot-water/heata-unit)

**Revenue recognition and size (Companies House accounts)**
- Accounting policy (FY2024 and FY2025 accounts): "Revenue from rendering computer services is recognised in the period in which the services are provided based on the work performed on agreed daily rates." Grants: "A grant that specifies performance conditions is recognised in income when the performance conditions are met." — [Bit Warmer Ltd accounts FY2025, filed 17 Apr 2026](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Accounts are "Total exemption full accounts" under the small companies regime (filleted). **No turnover or P&L is disclosed** — [Companies House filing history](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Trade debtors: £0 (31 Dec 2023), £6,718 (31 Dec 2024), £340 (31 Dec 2025). Other debtors: £149,025, £125,003 and £100,434 for the same dates — [accounts FY2024 and FY2025 iXBRL](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Tangible fixed assets: computers costing £4,590 in total, with net book value £1,989 at 31 Dec 2025. No plant or servers are capitalised — [FY2025 accounts](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Policy: "Research expenditure is written off against profits in the year in which it is incurred. Identifiable development expenditure is capitalised to the extent that the technical, commercial and financial feasibility can be demonstrated." — [same](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)

**Unit hardware**
- Unit dimensions: "36cm by 28cm compute servers installed on domestic hot water cylinders" — [DCD, Jan 2023](https://www.datacenterdynamics.com/en/news/civo-partners-with-heata-to-offer-batch-processing-on-digitized-boilers/)
- The power-draw basis of 330 W compute is given in the carbon footnote — [heata-unit page](https://www.heata.co/free-hot-water/heata-unit)
- MIT TR (Aug 2023) stated "No price for the unit or the service is given" — [MIT Technology Review](https://www.technologyreview.com/2023/08/18/1077548/computer-waste-heat/)

### Inferences
- **Revenue is very small.** Year-end trade debtors of £340–£6.7k and no capitalised server fleet, together with annual losses of about £375k–£610k, are consistent with commercial revenue in the low tens of thousands of £ a year at most. This is an inference from the balance sheet only, because turnover is not filed. The "agreed daily rates" wording suggests some revenue came from consulting-style or rendering services, not metered cloud usage.
- **Electricity cost per unit:** 330 W × 8,760 h × 80% ≈ 2,310 kWh a year. At roughly 22–25p/kWh, heata would credit about £510–£580 per unit per year at full modelled utilisation, and about £320–£360 at 50%. Compare this with the 2024 "Heavy" plan price of £210 per node per month (£2,520 a year). Gross margin per unit is positive only if a unit is sold at a meaningful share of list capacity. Electricity is therefore the dominant variable cost. Hardware, install, 4G/fibre connectivity and submeter capex come on top (not disclosed).
- The units do not appear on the balance sheet. They may be expensed as R&D, grant-funded (the Innovate UK project 10017625 funded "100 alpha prototypes"), or held off-balance-sheet. This is unverified.
- Grants (£791,590 awarded per GtR) equal roughly 45% of equity raised (about £1.75m of share premium). Public money has funded much of the hardware and trials.

### Gaps
- No disclosed turnover, gross margin, revenue per unit or per kWh, hardware cost per unit, install cost, or payback period.
- How the grants were split between income and liability each year cannot be seen in filleted accounts.
- Whether hosts are always credited the full electricity cost at their own tariff, or at a fixed rate, is not specified beyond "credited for the amount of energy".

---

## 4. Funding: grants, equity, investors, Centrica/British Gas

### Takeaway
Heata has raised about £2.1m of share premium in total plus about £0.79m in UKRI grants. The main round was a "£1 million seed" in Sept 2023, led by Civo CEO Mark Boost with Green Angel Syndicate. Small top-ups followed in 2024, 2025 and June 2026 at about £21.92 per share, which implies a valuation of roughly £3.8–4.1m. British Gas Trading Limited is a shareholder with about 8.2%. The founders each hold about 20%.

### Cited Findings
**Equity rounds**
- "We have closed a £1 million seed funding round … The round was led by Mark Boost of Civo, with remaining contributions from Green Angel Ventures and other angel investors. British Gas retains its stake in the business." The money was earmarked for "new hires in sales, marketing, design and IT" — [heata blog, 26 Sep 2023](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding). Corroborated by [Marriott Harrison (law firm)](https://www.marriottharrison.com/work/heata-raises-in-seed-round-funding-helping-to-reduce-carbon-emissions). Caplight lists "$1.25M" raised, "Seed round in September 2023" — [Caplight](https://www.caplight.com/company/heata)
- Green Angel Syndicate quote: "We are delighted to be investing in heata" — Magali Christensen, Investment Manager — [seed post](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding)
- Share premium on balance sheet: £0 (2020), £374,986 (2021), £539,427 (2022, restated), £1,590,626 (2023), £1,590,626 (2024), £2,115,539 (2025). This implies new equity of about £375k in 2021, about £1.05m in 2023 (the seed) and about £525k in 2025 — [accounts FY2021–FY2025](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Share allotments (SH01): 3 Jul 2024, 1,360 shares at £22.84; 31 Mar 2025 (to 170,470 shares); 4 May 2025, 2,016 shares at £21.924603; 19 Jun 2025, 1,368 shares at £21.92; 7 Jul 2025 (to 174,762); **10 Jun 2026, 10,335 shares at £21.92 (≈ £226.5k), giving 185,097 shares in total** — [Companies House SH01 filings](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history). The shares were sub-divided on 1 Nov 2023, which explains the jump from about 15k to about 150k shares.
- Earlier: Aug 2022 resolutions included removal of pre-emption rights and own-share purchase. Share buybacks were filed in 2022, Aug 2023 and Aug 2024 — [filing history](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- A loan from "a company with a common director" (interest-free in 2022) stood at £218,000 (2021), £313,500 (2022), £55,523 (2023), £57,498 (2024) and £59,543 (2025). The 2023 drop coincides with the seed round — [accounts](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)

**Shareholders (confirmation statement dated 3 Mar 2026, replacement filed 30 Sep 2026; 174,762 shares in issue)** — [CS01 RP01, 30 Sep 2026](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Christopher John Jordan 35,430 (≈20.3%); Michael James Paisley 35,430 (≈20.3%)
- **British Gas Trading Limited 14,280 (≈8.2%)**
- Build With Hubs Limited 10,580 (≈6.1%); it was the 75%+ PSC from Jun 2020 to Mar 2022. Zero One Venture Studio LLP holds 4,570 (≈2.6%); it was the 75%+ PSC from Jun 2019 to Jun 2020
- GAS BBI Nominees Ltd 9,320 and GAS CCF (TT) Nominee Limited 5,274
- Paul Mark Cresswell (ex-director) 6,890; Robin Klein 6,569; Russell Clive Beharrell 5,417; Paul Chase-Gardener 4,919; Viva Investment Group Ltd 4,370; Robert Clarke 3,534; JK Stewart Investments Pty Ltd 3,182; Founders Capital Nominees Ltd 2,016; Brookcap UK Ltd 1,825; plus about 25 other small holders (42 holdings in total)
- PSC register: "no registrable person" since 25 Jul 2023, when Jordan and Paisley ceased being >25% holders. This cessation was filed late, on 16 Mar 2026 — [PSC page](https://find-and-update.company-information.service.gov.uk/company/11110428/persons-with-significant-control)

**Centrica / British Gas relationship**
- Origin: "Founded in 2017 as a British Gas innovation project aimed at supporting people living in fuel poverty" — [seed post](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding). About page: "A friend was working with British Gas and supporting people in fuel poverty was one of the key areas for exploration" — [heata.co/about-us](https://www.heata.co/about-us)
- Equity: British Gas Trading Limited holds 14,280 shares (above). "British Gas retains its stake" (2023). The GtR Media Cymru abstract describes heata as "Backed by British Gas" — [GtR 10099681](https://gtr.ukri.org/projects?ref=10099681)
- Commercial: 10-unit employee trial in Feb 2025 (§1). The installation process was "tested by British Gas" engineers — [heata-unit page](https://www.heata.co/free-hot-water/heata-unit)

**Grants (UKRI Gateway to Research, organisation "BIT WARMER LIMITED")** — [GtR API, organisation 45FE7A8F-A252-4E52-BBBD-C774B4E8CA93](https://gtr.ukri.org/organisation/45FE7A8F-A252-4E52-BBBD-C774B4E8CA93)
| Ref | Title | Funder | Award (£) | Dates |
|---|---|---|---|---|
| 105712 | Distributed Data Centres (DDC) – Study | Innovate UK | 139,876 | Jan 2020 – Mar 2021 |
| 74471 | Distributed Data Centres – Feasibility | Innovate UK | 26,678 | Jun 2020 – Nov 2020 |
| 10017625 | Harnessing heat from compute: SAP Accreditation (partner: Sero Life Ltd) | Innovate UK | 418,595 | Feb 2022 – Sep 2023 |
| 10104998 | heata – SAP Accreditation Stage 5b | Innovate UK | 49,924 | Mar 2024 – Jul 2024 |
| 10099681 | heata x Media Cymru: Sustainable Render Hub (partners Bomper Studio, Kensa Contracting) | SiPF / Media Cymru | 156,517 | Mar 2024 – Sep 2026 (Active) |
| | **Total** | | **791,590** | |
- Project 10017625's stated goal: "BW will build 100 alpha prototypes and run a pilot in 100 homes for 12 months … to pursue SAP/RdSAP accreditation" — [GtR 10017625](https://gtr.ukri.org/projects?ref=10017625). Heata's own post (25 May 2022) calls it a "SMART Grant" and expects a "4 - 8 point improvement to a house's EPC". It pitches landlords on meeting EPC C by 2026/2028 — [heata blog](https://www.heata.co/content-hub/heata-awarded-innovate-uk-smart-grant-in-partnership-with-sero-homes)
- Media Cymru render farm: "funded by Media Cymru through its Greening the Screen grant". It uses Kensa (heat network) and was intended to heat "a social housing estate in the CCR". It was ultimately deployed to heat Y Bank, a community building in Caerphilly — [GtR 10099681](https://gtr.ukri.org/projects?ref=10099681); [heata.co/render/mediacymru](https://www.heata.co/render/mediacymru)
- Programme support: heata is "part of the Innovate UK Net Zero Group" — [heata.co/free-hot-water](https://www.heata.co/free-hot-water). It is also in the Microsoft for Startups, Google for Startups and Nvidia Inception programmes (logos on the compute page)

**Crowdfunding**
- No equity crowdfunding campaign was found. The /investors page invites "impact investing" registrations of interest — [heata.co/investors](https://www.heata.co/investors)

### Inferences
- Implied post-money valuation at £21.92 per share is about £3.83m on 174,762 shares (2025) and about £4.06m on 185,097 shares (Jun 2026). The 2024 price of £22.84 means 2025–26 money came in flat to slightly down. This suggests no priced institutional Series A, only small angel top-ups.
- "GAS BBI Nominees" and "GAS CCF (TT) Nominee" are very likely Green Angel Syndicate vehicles (BBI is probably British Business Investments co-investment; CCF is probably the Clean Growth / co-investment fund). This is unverified. Mark Boost does not appear by name, so his investment may sit in a nominee or corporate vehicle (unverified).

### Gaps
- Exact seed terms (SEIS/EIS, valuation) and the date British Gas got its stake (possibly at founding in 2017–2019) were not confirmed.
- What SOSE support for the Scotland expansion amounted to (Oct 2024) is unknown. No SOSE grant record was found.
- Any 2026 pilot-contract revenue from government is not disclosed.

---

## 5. Scale, status, people, and pivot/shutdown check (as of 2026-11-21)

### Takeaway
Heata is **active, not dissolved, and has no charges**. It is still tiny: an average of 7 employees in 2025, net assets of £96k and cash of £117k at 31 Dec 2025. Accumulated losses were £2.18m and losses ran at about £375k a year. That gives a cash runway of only months, which the June 2026 raise of about £227k extended slightly. The last hard deployment figure is **~80 units installed (Aug 2023), with 30 more planned**. No newer fleet count has been published. Heata's website still runs, with an Oct 2026 news post, but its jobs page shows no openings. There is no sign of shutdown. Instead there was a pivot from home-hot-water-only to "green compute" for government and enterprise, plus a GPU render farm heating a community building.

### Cited Findings
**Corporate status (Companies House, retrieved 2026-11-21)** — [Bit Warmer Ltd overview](https://find-and-update.company-information.service.gov.uk/company/11110428)
- BIT WARMER LIMITED, no. 11110428. Incorporated 13 Dec 2017. Status: **Active**. Private limited company. SIC 63990. Registered office: Wood Farm, Portsmouth Road, Godalming, GU7 2JR
- Last accounts were made up to 31 Dec 2025 (filed 17 Apr 2026). Next accounts are due 30 Sep 2027. The confirmation statement is up to date (3 Mar 2026). **0 charges registered** — [charges](https://find-and-update.company-information.service.gov.uk/company/11110428/charges)
- No insolvency, administration or strike-off filings appear in the filing history up to the 30 Sep 2026 replacement CS01 — [filing history](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Officers: Christopher John Jordan (director since 17 Aug 2020, born Nov 1974); Michael James Paisley (since 8 Sep 2021); Charlie Beharrell (since 1 Jun 2023). Past directors: Mark Bjornsgaard (2017–2019), Ruth Brougham (2017–2021), Finn McCabe (2019–2021), Paul Cresswell (2021–2022), Paul Welsh (2017–2018) — [officers](https://find-and-update.company-information.service.gov.uk/company/11110428/officers)

**Financial trajectory (balance sheet, £, at 31 Dec)** — [accounts FY2018–FY2025](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
| Year | Cash | Net assets | Accumulated losses | Avg employees |
|---|---|---|---|---|
| 2018 | 291 | 67,588 | (307,512) | 2 |
| 2019 | 97 | 33,979 | (341,121) | 2 |
| 2020 | 11,166 | (3,270) | (378,370) | 2 |
| 2021 | 43,475 | (211,205) | (586,305) | 4 |
| 2022 | 16,538 | (235,720) | (806,095) | 9 |
| 2023 | 362,752 | 399,157 | (1,191,618) | 7 |
| 2024 | 288,277 | 283,649 | (1,802,065) | 8 |
| 2025 | 116,647 | 96,077 | (2,176,650) | 7 |
- The 2021 accounts state the losses explicitly: £37,249 for 2020 and £207,935 for 2021 — [FY2021 accounts](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)
- Going concern (FY2024 and FY2025): "the directors have a reasonable expectation that the company has adequate resources to continue in operational existence for the foreseeable future." — [FY2025 accounts](https://find-and-update.company-information.service.gov.uk/company/11110428/filing-history)

**Deployed units over time**
- 2020–21: the Innovate UK study aimed to build "the first TRL8 operational Hot Patch system for trialling in a series of homes" — [GtR 105712](https://gtr.ukri.org/projects?ref=105712)
- May 2022: a planned "MVP in 100 homes as a pre-commercial pilot" — [heata blog, 25 May 2022](https://www.heata.co/content-hub/heata-awarded-innovate-uk-smart-grant-in-partnership-with-sero-homes)
- Aug 2023: "To date, 80 units have been installed", with "30 more slated … by the end of October", in Surrey. The trial had run "for more than a year" — [MIT Technology Review, 18 Aug 2023](https://www.technologyreview.com/2023/08/18/1077548/computer-waste-heat/). Stale.
- CB Insights (undated aggregator) says about 100 homes, per the search snippet — [CB Insights](https://www.cbinsights.com/company/heata). Unverified.
- Feb 2025: +10 units (British Gas employee trial) — [Centrica](https://www.centrica.com/media-centre/news/2025/british-gas-partners-with-heata-on-trial-to-reuse-waste-heat-from-data-processing/)
- 2024 PAYG plan capped customers at "Nodes Up to 20", and the reserved plans at "Up to 50" — [Wayback Jun 2024](https://web.archive.org/web/20240623112054/https://www.heata.co/compute)
- Ambition statements are market-sizing, not targets: "The waste heat from one data centre could provide hot water for 100,000 homes" — [heata.co](https://www.heata.co/). No dated unit target ("X homes by 20YY") was found.

**Activity and status signals in 2026**
- Latest news post: Pitch in Whitehall win, 9 Oct 2026. The previous post was the Ray article on 4 Jul 2025, a 15-month gap — [heata content hub](https://www.heata.co/content-hub)
- New 2026 assets: the Media Cymru render portal (sitemap lastmod 1 Oct 2026); a new SLA ("Last Updated: August 2026"); a new per-resource price list and heata CLI docs (example output dated 2026-03-24) — [heata.co/render/mediacymru](https://www.heata.co/render/mediacymru); [docs.heata.co](https://docs.heata.co/services/spot-vms/)
- Jobs: "There are no positions currently available." — [heata.co/jobs](https://www.heata.co/jobs)
- The company has a LinkedIn page (heatacompute), but its employee count was not retrieved — [LinkedIn](https://uk.linkedin.com/company/heatacompute)
- Third-party 2026 mention: Startup Fortune (25 Jul 2026) says Heata "has been running a quieter version of the same idea since 2022", covers electricity and maintenance, and has a British Gas trial. It gives no unit counts — [Startup Fortune](https://startupfortune.com/startups-are-paying-homeowners-to-host-ai-compute-nodes-as-electricity-costs-spiral/)

**Founder statements**
- Chris Jordan (co-founder & CTO; MIT TR calls him a physicist): "Data centres are fundamental to our modern lives but they do use (and waste) enormous amounts of energy … heat is useful, why waste it?" (Sep 2023) — [seed post](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding). And: "With a small change to where they place their data processing, businesses throughout the UK could be supporting their communities as a byproduct of their cloud computing." (Feb 2025) — [Centrica](https://www.centrica.com/media-centre/news/2025/british-gas-partners-with-heata-on-trial-to-reuse-waste-heat-from-data-processing/)
- Jordan (Jan 2023): "I am particularly committed to being the bridge between the world of tech and areas like social housing" — [DCD](https://www.datacenterdynamics.com/en/news/civo-partners-with-heata-to-offer-batch-processing-on-digitized-boilers/)
- Jordan (Oct 2024): "adding the Expanso platform … is making it easier for our cloud customers to access Heata compute, and broadening our target markets." — [heata x Expanso](https://www.heata.co/compute/heata-and-expanso-team-up-to-expand-green-cloud-to-traditional-workloads)
- Michael Paisley (co-founder, Chief Creative Officer, designer) describes the model as a "diffuse data center" — [MIT TR, Aug 2023](https://www.technologyreview.com/2023/08/18/1077548/computer-waste-heat/)
- The seed post refers sales enquiries to "Book a meeting with Charlie", presumably Charlie Beharrell, director since Jun 2023 — [seed post](https://www.heata.co/content-hub/announcement-weve-just-secured-1-million-in-funding)

### Inferences
- Losses implied by the change in accumulated losses: about £385k (2023), £610k (2024) and £375k (2025). The 2022/23 figures include a prior-period adjustment, so treat them as approximate. Year-end 2025 cash of £117k against a burn of roughly £375k a year implies only about 4 months' runway. The £227k raised in Jun 2026 adds about 7 more months at the same burn. Heata is probably raising money or cutting costs in late 2026; this is unverified.
- The fleet has probably stayed at about 100 home units since 2023: 80 installed, about 30 planned and 10 for British Gas. There is no announced scale-up, and the 2024 node caps were 20–50. At 7 staff and a small hardware budget, a fleet in the hundreds is unlikely without a new capital source.
- The strategy has shifted. The emphasis moved from social-housing EPC accreditation (2022–24) to selling "green compute" to enterprise and government (2025–26). The Media Cymru GPU farm heats one building instead of homes, which is a step toward clustered or non-domestic heat sinks.

### Gaps
- No current (2025–26) count of deployed or active units, fleet utilisation, or hot-water delivered. A "8 million liters of hot water" figure appeared only in a search-engine summary with no traceable source, so it is excluded.
- Turnover, gross margin and headcount by function are not disclosed (filleted small-company accounts).
- No founder podcast or conference-talk transcripts with business metrics were found in this pass.
- The outcome of SAP/RdSAP accreditation (whether heata units count in EPCs) was not found.
- DCD's Feb 2025 article on British Gas and Heata could not be retrieved (Cloudflare block). The Centrica original was used instead.

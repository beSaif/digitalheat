# Prices and costs: research notes (DigitalHeat business case)

All figures were seen on **2026-11-21** unless the row gives another date. Cloud prices are on-demand list prices in USD without VAT or discounts. Region codes: **ZRH** is AWS eu-central-2 / GCP europe-west6 (Zurich); **FRA** is AWS eu-central-1 / GCP europe-west3 (Frankfurt); **GLB** means Google charges one global price.
FX (SNB, monthly average Oct 2026): 1 USD = 0.8285 CHF, 1 EUR = 0.9284 CHF ([SNB data portal](https://data.snb.ch/en/topics/ziredev/cube/devkum)).
AWS numbers come from the machine-readable AWS Price List API (`pricing.us-east-1.amazonaws.com/offers/v1.0/aws/<service>/current/<region>/index.json`) unless noted, which is the same data that the AWS pricing pages show.

## A. Cloud list prices for the equivalent managed service

| # | Item | Value | Unit | Region | Source | How solid |
|---|---|---|---|---|---|---|
| 1 | AWS Bedrock, Amazon Titan Text Embeddings V2 | 0.027 | USD / 1M input tokens | ZRH | [AWS Price List, AmazonBedrock eu-central-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-central-2/index.json) | Solid (official price file, published 2026-11-11). The FRA file lists 0.20, about 10× more, which looks like a legacy SKU |
| 1 | AWS Bedrock, Cohere Embed 4 | 0.12 | USD / 1M input tokens | ZRH | [AWS Price List, AmazonBedrockFoundationModels eu-central-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrockFoundationModels/current/eu-central-2/index.json) | Solid |
| 1 | AWS Bedrock, Cohere Embed 3 (English or Multilingual) | 0.10 | USD / 1M input tokens | FRA | same offer, eu-central-1 | Solid |
| 1 | Vertex AI, Gemini Embedding (online / batch) | 0.15 / 0.12 | USD / 1M input tokens | GLB | [Vertex AI pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing) | Solid (official page) |
| 1 | Vertex AI, text embeddings other than Gemini (text-embedding-005 etc.), online | 0.025 | USD / 1M input characters (listed as $0.000025 per 1k) | GLB | same | Solid. Note the unit is characters, not tokens |
| 2 | AWS Bedrock, Amazon Rerank v1 | 1.00 | USD / 1,000 queries ("search units") | FRA (not offered in ZRH) | [AWS Price List, AmazonBedrock eu-central-1](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/eu-central-1/index.json) | Solid |
| 2 | AWS Bedrock, Cohere Rerank 3.5 | 2.00 | USD / 1,000 queries | FRA | AmazonBedrockFoundationModels eu-central-1 | Solid |
| 2 | Google Vertex AI Ranking API | 1.00 | USD / 1,000 queries (1 query = up to 100 documents) | GLB | [Agent Search / AI Applications pricing](https://cloud.google.com/generative-ai-app-builder/pricing) | Solid |
| 3 | Amazon Rekognition Image, DetectLabels (Group 2 API), first 1M images per month | 1.20 | USD / 1,000 images | FRA (not offered in ZRH) | [AWS Price List, AmazonRekognition eu-central-1](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRekognition/current/eu-central-1/index.json) | Solid. Image Properties adds 0.90 / 1,000 |
| 3 | Google Cloud Vision, Label Detection (1,001 to 5M per month; first 1,000 free) | 1.50 | USD / 1,000 images | GLB | [Cloud Vision pricing](https://cloud.google.com/vision/pricing) | Solid |
| 4 | Amazon Rekognition Video, stored-video analysis (labels and people) | 0.12 | USD / minute | FRA | AmazonRekognition eu-central-1 | Solid. Live streams cost 0.144 / min |
| 4 | Google Video Intelligence, Person detection (above 1,000 free min per month) | 0.10 | USD / minute | GLB | [Video Intelligence pricing](https://cloud.google.com/video-intelligence/pricing) | Solid. Label detection 0.10, object tracking 0.15 |
| 5 | Amazon Transcribe, standard batch | 0.006 (0.0001 / s) | USD / minute | ZRH | [AWS Price List, transcribe eu-central-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/transcribe/current/eu-central-2/index.json), [Transcribe pricing](https://aws.amazon.com/transcribe/pricing/) | Solid. The same rate applies in FRA and us-east-1. This is a big cut from the older 0.024 / min that many articles still quote |
| 5 | Google Speech-to-Text V2, standard (0 to 500k min per month) | 0.016 | USD / minute | GLB | [Speech-to-Text pricing](https://cloud.google.com/speech-to-text/pricing) | Solid |
| 5 | Google Speech-to-Text V2, dynamic batch (low urgency) | 0.003 | USD / minute | GLB | same | Solid |
| 6 | AWS Elemental MediaConvert, Basic tier, AVC ≤30 fps, SD | 0.0085 | USD / output minute | FRA (not offered in ZRH) | [AWS Price List, AWSElementalMediaConvert eu-central-1](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSElementalMediaConvert/current/eu-central-1/index.json) | Solid |
| 6 | AWS Elemental MediaConvert, Basic tier, AVC ≤30 fps, HD | 0.0085 (new SKU) / 0.017 (legacy SKU) | USD / output minute | FRA | same | Medium. The file lists both SKUs and it is unclear which applies to a new account. Use 0.017 to be conservative |
| 6 | Google Transcoder API, SD / HD / UHD | 0.015 / 0.030 / 0.060 | USD / output minute | GLB | [Transcoder pricing](https://cloud.google.com/transcoder/pricing) | Solid |
| 7 | AWS EC2 c7i.16xlarge (64 vCPU, 128 GiB), Linux on-demand | 3.585 (= 0.0560 / vCPU-h) | USD / hour | ZRH | [AWS EC2 pricing JSON, EU (Zurich)](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Zurich)/Linux/index.json) | Solid. FRA: 3.259 |
| 7 | AWS EC2 c7i.8xlarge (32 vCPU) / c7i.48xlarge (192 vCPU) | 1.793 / 10.756 | USD / hour | ZRH | same | Solid |
| 7 | AWS EC2 c7i.16xlarge, spot | about 1.13 (35% of on-demand) | USD / hour | FRA (no ZRH spot data) | [AWS Spot Instance Advisor data](https://website.spot.ec2.aws.a2z.com/spot.js) | Medium. Spot prices change all the time |
| 7 | GCP c3-standard-44 (44 vCPU, 176 GB), on-demand / spot | 2.617 / 0.957 | USD / hour | FRA (c3 is not offered in ZRH) | [gcloud-compute.com](https://gcloud-compute.com/c3-standard-44.html) (third-party, built from the Google SKU catalog, updated 2026-11-18) | Medium to solid |
| 7 | GCP c4-standard-48 (48 vCPU), on-demand / spot | 3.108 (= 0.0647 / vCPU-h) / 1.864 | USD / hour | ZRH | [gcloud-compute.com europe-west6](https://gcloud-compute.com/europe-west6.html) | Medium to solid |
| 7 | AWS EC2 g6.xlarge (1× NVIDIA L4, 4 vCPU) | 1.085 | USD / hour | ZRH | AWS EC2 pricing JSON, EU (Zurich) | Solid. FRA: 1.006 |
| 7 | AWS EC2 g5.xlarge (1× NVIDIA A10G) | 1.258 | USD / hour | FRA (not offered in ZRH) | [AWS EC2 pricing JSON, EU (Frankfurt)](https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/EU%20(Frankfurt)/Linux/index.json) | Solid |
| 8 | AWS RDS PostgreSQL db.m7g.large, Single-AZ vs Multi-AZ | 0.221 vs 0.442 (exactly 2.0×) | USD / hour | ZRH | [AWS Price List, AmazonRDS eu-central-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/eu-central-2/index.json) | Solid. AWS charges a full second copy for redundancy |
| 8 | S3 Standard storage (first 50 TB) | 0.02695 | USD / GB-month | ZRH | [AWS Price List, AmazonS3 eu-central-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/eu-central-2/index.json) | Solid |
| 8 | S3 One Zone-IA vs Standard-IA (one AZ vs several AZs) | 0.01188 vs 0.01485 (+25% for multi-AZ) | USD / GB-month | ZRH | same | Solid |
| 8 | S3 Cross-Region Replication, ZRH to FRA | second copy of storage (about 2×) + 0.02 / GB inter-region transfer + 0.015 / GB if Replication Time Control is used | USD | ZRH to FRA | AmazonS3 and [AWSDataTransfer eu-central-2](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/eu-central-2/index.json) price lists | Solid |

Azure was not collected. It was optional, and AWS and GCP already set the price band.

## B. Hardware capex

| # | Item | Value | Unit | Source | How solid |
|---|---|---|---|---|---|
| 1 | ~1 kW dual-socket CPU server: 2× AMD EPYC 9555 (64 cores, 360 W each) + 512 GB DDR5 + NVMe, at 2026 memory prices | 36,000 to 43,000 (about CHF 30–36k) | USD per server | Estimate built from parts: CPUs 2 × 7,973 ([AMD 1ku list price](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9555.html)); RAM 8 × 64 GB at 1,600–2,560 (see B2); 2U barebone from about EUR 5,700–6,500 ([Thomas-Krenn RA2212](https://www.thomas-krenn.com/en/products/rack-server/2u-servers/amd-dual-cpu)) | Estimate. No public configured quote was found. Memory is now 35–50% of the bill of materials |
| 1 | Cheaper variant: 2× EPYC 9355 (32 cores, 280 W each) + 512 GB, about 0.75 kW at the wall | 26,000 to 33,000 | USD per server | Estimate. 9355 CPU about 3,000 retail ([CDW](https://www.cdw.com/product/amd-epyc-9355-server-cpu/8383737)) | Estimate |
| 1 | ~1 kW GPU server: 1× NVIDIA RTX PRO 6000 Blackwell Server Edition (600 W) + single-socket EPYC host | 25,000 to 35,000 | USD per server | GPU about 11,989 ([Newegg](https://newegg.com/p/N82E16814132104)), plus a host at about 13–20k (estimate) | Estimate |
| 1 | Server list-price trend | Dell raised list prices about 17% across PowerEdge on 2026-03-30. A 512 GB 2U reference build index went from 100 (Jan 2025) to about 205 (Jul 2026) | % | [Servnet UK server price index](https://www.servnetuk.com/research/enterprise-server-price-index-2026) | Medium (reseller index, described as indicative) |
| 2 | Server DRAM contract price, quarter on quarter (TrendForce) | 1Q26 > +60% (forecast); 2Q26 +53–58% (actual ASP); 3Q26 +13–18% (forecast); 4Q26 +10–15% (conventional DRAM forecast) | % QoQ | [TrendForce 2026-01-05](https://www.trendforce.com/presscenter/news/20260105-12860.html), [2Q26 revenue report via iConnect007](https://iconnect007.com/article/151492/dram-revenue-rises-595-qoq-in-2q26-as-supply-trails-demand/151489/ein), [TrendForce 2026-07-09](https://www.trendforce.com/presscenter/news/20260709-13140.html), [TrendForce 2026-09-30](https://www.trendforce.com/presscenter/news/20260930-13258.html) | Solid (primary analyst). Compounded, 4Q25 to 4Q26 is about **3.0–3.4×**, so the case owner's "2.5× in a year" holds and is if anything low |
| 2 | 64 GB DDR5 RDIMM, retail, new | 2,561 (= 40 / GB). It was 2,245 on 2026-10-27 | USD per module | [Capital & Compute tracker](https://capitalandcompute.net/memory-prices/server/) (Amazon US listing, 2026-11-16) | Medium. A single-retailer street price, higher than what OEMs pay on contract |
| 2 | 64 GB DDR5 RDIMM, contract-like | 873 (Q1 2026), projected 1,586 (Q4 2026) | USD per module | Citi note of 2026-05-12, as quoted in search results (primary not seen) | Low to medium |
| 2 | 64 GB DDR5-4800 RDIMM, early 2025 vs now | about 380 → 820–890 | USD per module | [DatacenterDisk 2026-10-11](https://datacenterdisk.com/news/memory-chip-shortage-2026-server-ram-prices) | Medium |
| 3 | ZutaCore HyperCool price | not public | — | [ZutaCore FAQ / solutions](https://zutacore.com/solutions) (claims only "50% TCO reduction") | Not available. Ask ZutaCore for a quote |
| 3 | Proxy: direct liquid cooling capex premium | +5–10% of facility capex for new builds | % | Uptime Institute estimate, quoted in a search snippet of a paywalled UII update | Low to medium. Proxy |
| 3 | Proxy: direct-to-chip premium over air cooling | +2,500 to 4,500 | USD / kW | [Core Insights Review 2026-09-01](https://www.coradvisors.net/2026/09/liquid-vs-air-cooling-cost-comparison-data-centers-2026.html), quoting an unnamed "2026 enterprise TCO guide" | Low. Proxy, data-centre scale |
| 3 | Our planning value: cold plates, manifold and small CDU / heat exchanger for 1 kW | 1,500 to 3,000 | CHF / kW | Estimate built from the proxies above | Estimate |
| 4 | Dry cooler, large: Kelvion LF-PD203T4H, 516 kW at 55→42 °C fluid, 32 °C air | 33,923 list (= 66 / kW); fans 6 × 1.708 kW = 10.25 kW (= **0.020 kW_el per kW_th**) | EUR | [Kelvion datasheet (Mar 2023)](https://www.resale.de/images/161618957_g_rueckkuehler-lf-pd203t4h-080y06d_2023-04-dn100.pdf) | Solid for fan power. Price is 2023 list and for a large unit |
| 4 | Dry cooler, small: 18.5 kW unit in a Swiss building permit | 7,365 list excl. VAT (= about 400 / kW); about 0.47 kW electric (about 0.025 kW/kW) | EUR | St. Gallen building permit noise report, offer dated 2023-12-07 ([stadt.sg.ch PDF](https://www.stadt.sg.ch/content/dam/dokument_library/dpb/abb/baubewilligungen/63335-holzstrasse-3a/09%20L%C3%A4rmschutznachweise.pdf), now offline; read through a search snippet) | Medium |
| 4 | Our planning value for a 5–10 kW dry cooler at about 60 °C water | 3,000 to 5,000 for the unit + 1,000 to 2,000 to install; fans about 0.01–0.03 kW_el per kW_th at the design point and less on average over a year (60 °C water gives a large ΔT to outside air) | CHF | Estimate scaled from the two rows above | Estimate |
| 5 | 1,000 L buffer tank, retail, without / with heat exchanger and insulation | 899 to 1,476 | EUR | [Klimaworld SPS 1000](https://www.klimaworld.com/products/schichten-pufferspeicher-klimaworld-1000-liter), [EPSR 1000](https://www.klimaworld.com/products/energie-pufferspeicher-klimaworld-1000-liter-1-warmetauscher) (German retail) | Medium (German retail, no Swiss quote) |
| 5 | 1,000 L buffer tank installed in Switzerland, including insulation and connection | 3,000 to 5,000 | CHF | Estimate (one German guide quotes about EUR 3,000 for 1,000 L) | Estimate |
| 5 | Connecting the server rack to the building heating loop: heat exchanger, pump, valves, piping, controls, 2–4 installer-days | 5,000 to 15,000 | CHF per site | Estimate, no public source | Estimate. Get a quote from a Basel installer |

## C. Operating costs

| # | Item | Value | Unit | Source | How solid |
|---|---|---|---|---|---|
| 1 | Electricity 2026, IWB Basel, household H4 (5-room flat, 4,500 kWh/yr) | **33.25** (grid 11.41 + energy 10.89 + municipal charges 7.44 + grid surcharge 2.3) | Rp/kWh incl. VAT | [ElCom Strompreis API / site](https://www.strompreis.elcom.admin.ch/) (GraphQL query, municipality 2701 Basel) | Solid (official). Confirms our value |
| 1 | Electricity 2026, IWB Basel, business C2 (30,000 kWh/yr, ≤15 kW) | **32.75** (grid 13.11 + energy 10.03 + charges 7.13 + 2.3) | Rp/kWh | same | Solid |
| 1 | Electricity 2026, IWB Basel, business C3 (150,000 kWh/yr, 50 kW) | **32.43** (grid 13.57 + energy 9.39 + charges 6.98 + 2.3) | Rp/kWh | same | Solid. ElCom says 2027 tariffs fall about 4% on average nationally; Basel 2027 values were not in the API yet |
| 2 | Server hardware incidents | about 8% of servers have at least one hardware repair per year; 78% of replaced parts were hard disks | % per year | [Vishwanath & Nagappan, Microsoft Research, SoCC 2010](https://www.microsoft.com/en-us/research/wp-content/uploads/2010/06/socc088-vishwanath.pdf) (100,000+ servers) | Medium (old, HDD-heavy fleet; SSD-only servers will be lower) |
| 2 | Drive annualised failure rate | 1.36% (2025), 1.24% (Q1 2026) | % per year | [Backblaze Drive Stats](https://www.backblaze.com/blog/backblaze-drive-stats-for-2025/) | Solid (HDDs) |
| 2 | Hardware maintenance contract | third party about 8–15% of purchase price per year (next business day); OEM about 20% | % of capex per year | [ICD3S blog](https://icd3s.com/blog/third-party-server-maintenance-vs-oem-contracts-cost-savings/) (vendor) | Low to medium. Planning value: 10% per year after the warranty period |
| 3 | Server useful life, hyperscalers | AWS cut a subset from 6 to 5 years from 2025-01-01; Meta 5.5 years (2025); Microsoft and Alphabet 6 years | years | [Accounting Today on Meta](https://www.accountingtoday.com/articles/metas-accounting-move-on-ai-servers-to-boost-profit), [Deep Quarry on Amazon](https://deepquarry.substack.com/p/amazon-revises-server-lifespan-amid) | Solid (company filings, quoted by press) |
| 3 | Swiss tax write-off, IT hardware | 40% per year declining balance (= 20% straight line, about 5 years) | % per year | ESTV Merkblatt A 1995 ([copy at Uni Basel](https://eskript.ius.unibas.ch/wp-content/uploads/sites/35/2017/01/estv-merkblatt_a_1995.pdf)) | Solid. Planning value: write off over 5 years |

## D. Heating comparison for Swiss homeowners

| # | Item | Value | Unit | Source | How solid |
|---|---|---|---|---|---|
| 1 | Air-to-water heat pump, single-family house, installed with storage | 45,000 to 60,000 | CHF | [EnergieSchweiz](https://www.energieschweiz.ch/wohnen/heizungssysteme/waermepumpen/) | Solid (federal programme). Other Swiss sites give a lower 30–40k: [Helion](https://www.helion.ch/de/ratgeber/waermepumpe/luft-wasser-waermepumpe/), [hausinfo](https://hausinfo.ch/de/bauen-renovieren/haustechnik-vernetzung/heizung-lueftung-klima/waermepumpen/investitionskosten.html) |
| 1 | Ground-source heat pump, single-family house | 55,000 to 80,000 | CHF | EnergieSchweiz (same page) | Solid |
| 1 | Basel-Stadt subsidy, air-to-water heat pump, outside the district-heating area | 8,000 + 250 per kW_th (a 10 kW unit gets CHF 10,500); at most 40% of the investment | CHF | [bs.ch Förderbeiträge Wärmepumpen](https://www.bs.ch/wsu/aue/abteilung-energie/foerderbeitraege-energie/waermepumpen) | Solid |
| 1 | Basel-Stadt subsidy, inside the district-heating area (≤70 kW) | 4,000 + 125 per kW_th (halved from 2025-06-01) | CHF | same | Solid |
| 1 | Basel-Stadt subsidy, ground-source heat pump outside district heating, ≤10 kW | up to 30,000 | CHF | same | Solid |
| 2 | Annual running cost, air-to-water heat pump, single-family house | 1,000 to 1,600 | CHF / yr | EnergieSchweiz (same page) | Solid. The case value of ~1,500 CHF/yr sits in this range |
| 2 | Annual running cost, oil heating (2,500 L/yr, 1980 house, 160 CHF per 100 L in Sep 2026, above 170 since) | about 4,000 | CHF / yr | [MyKY / hausinfo, updated 2026-11-02](https://www.myky.ch/de/bauen-und-sanieren/haustechnik/oelheizung?hi=1) | Solid (energy only, no servicing) |
| 2 | Annual energy cost for 20,000 kWh of heat: oil vs ground-source heat pump | about 3,300 vs about 900 | CHF / yr | [UBS heating-replacement guide](https://www.ubs.com/ch/de/services/guide/mortgages-and-financing/articles/heating-replacement-tips.html) (table about 2 years old) | Medium |
| 2 | Cross-check: 20,000 kWh of heat at SPF 3.0 and 33.25 Rp/kWh | about 2,200 | CHF / yr | Our calculation | Calculation |
| 3 | Air-to-water heat pump efficiency, Swiss field test (heating + hot water), 2022/23 season | average **3.19** (range 2.47–4.04); ground-source average 4.26 | SPF (seasonal COP) | [BFE / OST field measurement report](https://pubdb.bfe.admin.ch/de/publication/download/11629) | Solid (measured). Earlier seasons gave 3.0 (2020/21) and 3.3 (2019/20). The case's 2.5 is a conservative value for old houses with high flow temperatures |

## Caveats

- **Region gaps:** Rekognition, MediaConvert, Bedrock Rerank, Cohere Embed 3, g5 and GCP c3 are not offered in Zurich, so the table uses Frankfurt prices for those. The Google AI APIs have one global price.
- **The unit of work differs between providers:** Vertex text-embedding-005 is billed per character, Gemini Embedding and Bedrock per token (roughly 1 token ≈ 4 characters in English). Rerank "queries" on both clouds mean up to 100 documents per query.
- **AWS Transcribe is now 0.006 USD/min** in the official price list, not the 0.024 that older articles quote. Check which one any competitor comparison assumes.
- **CPU-hour comparisons:** one dual EPYC 9555 server has 128 cores / 256 threads, about 4× c7i.16xlarge, which would cost about 14 USD/h on demand in Zurich. Compare on benchmarked work done, not raw vCPU counts.
- **DRAM prices move every week.** The server capex rows are estimates built from parts at November 2026 prices, roughly double what the same build cost in 2024. Get a real quote before any investor meeting.
- **The cooling, dry cooler, buffer tank and plumbing numbers are estimates or proxies.** No ZutaCore price is public, and small dry cooler prices are scaled from one 2023 Swiss offer and one large Kelvion unit.
- The maintenance percentages come from vendors who sell maintenance, so treat them as rough.
- Prices exclude VAT unless stated. ElCom tariffs include VAT.

```yaml numbers
# meta
date_seen: "2026-11-21"
fx_usd_chf: 0.8285          # SNB Oct 2026 avg
fx_eur_chf: 0.9284
# A1 embeddings
aws_bedrock_titan_embed_v2_usd_per_1m_tokens_zrh: 0.027
aws_bedrock_cohere_embed4_usd_per_1m_tokens_zrh: 0.12
aws_bedrock_cohere_embed3_usd_per_1m_tokens_fra: 0.10
gcp_gemini_embedding_usd_per_1m_tokens: 0.15
gcp_gemini_embedding_batch_usd_per_1m_tokens: 0.12
gcp_text_embedding_005_usd_per_1m_chars: 0.025
# A2 rerank
aws_bedrock_amazon_rerank_usd_per_1k_queries_fra: 1.00
aws_bedrock_cohere_rerank35_usd_per_1k_queries_fra: 2.00
gcp_ranking_api_usd_per_1k_queries: 1.00
# A3 image labels
aws_rekognition_detectlabels_usd_per_1k_images_fra: 1.20
gcp_vision_label_usd_per_1k_images: 1.50
# A4 video / people
aws_rekognition_video_usd_per_min_fra: 0.12
gcp_video_person_detection_usd_per_min: 0.10
# A5 speech-to-text
aws_transcribe_usd_per_min: 0.006
gcp_stt_v2_standard_usd_per_min: 0.016
gcp_stt_v2_dynamic_batch_usd_per_min: 0.003
# A6 transcoding
aws_mediaconvert_basic_sd_usd_per_min_fra: 0.0085
aws_mediaconvert_basic_hd_usd_per_min_fra: 0.017   # legacy SKU; new SKU 0.0085
gcp_transcoder_sd_usd_per_min: 0.015
gcp_transcoder_hd_usd_per_min: 0.030
# A7 compute
aws_c7i_16xlarge_usd_per_h_zrh: 3.585
aws_c7i_8xlarge_usd_per_h_zrh: 1.793
aws_c7i_48xlarge_usd_per_h_zrh: 10.756
aws_c7i_usd_per_vcpu_h_zrh: 0.0560
aws_c7i_16xlarge_spot_usd_per_h_fra: 1.125
gcp_c3_standard_44_usd_per_h_fra: 2.617
gcp_c3_standard_44_spot_usd_per_h_fra: 0.957
gcp_c4_standard_48_usd_per_h_zrh: 3.108
gcp_c4_standard_48_spot_usd_per_h_zrh: 1.864
gcp_c4_usd_per_vcpu_h_zrh: 0.0647
aws_g6_xlarge_usd_per_h_zrh: 1.085
aws_g5_xlarge_usd_per_h_fra: 1.258
# A8 redundancy
aws_rds_multi_az_multiplier: 2.0
aws_s3_standard_usd_per_gb_month_zrh: 0.02695
aws_s3_one_zone_ia_usd_per_gb_month_zrh: 0.01188
aws_s3_standard_ia_usd_per_gb_month_zrh: 0.01485
aws_interregion_transfer_usd_per_gb_zrh: 0.02
aws_s3_rtc_usd_per_gb: 0.015
# B capex (estimates unless noted)
server_cpu_1kw_usd_low: 36000      # estimate
server_cpu_1kw_usd_high: 43000     # estimate
server_cpu_budget_usd_low: 26000   # estimate
server_cpu_budget_usd_high: 33000  # estimate
server_gpu_1kw_usd_low: 25000      # estimate
server_gpu_1kw_usd_high: 35000     # estimate
amd_epyc_9555_usd_1ku: 7973
dram_server_multiple_4q25_to_4q26_low: 3.0   # compounded TrendForce QoQ
dram_server_multiple_4q25_to_4q26_high: 3.4
ddr5_rdimm_64gb_usd_retail: 2561
ddr5_rdimm_64gb_usd_contract_q4_2026: 1586   # Citi projection, low confidence
dlc_chf_per_kw_low: 1500           # estimate / proxy
dlc_chf_per_kw_high: 3000          # estimate / proxy
dry_cooler_10kw_chf_low: 3000      # estimate, unit only
dry_cooler_10kw_chf_high: 5000     # estimate, unit only
dry_cooler_install_chf: 1500       # estimate
dry_cooler_fan_kw_per_kw: 0.02     # Kelvion datasheet, design point
buffer_tank_1000l_eur_retail_low: 899
buffer_tank_1000l_eur_retail_high: 1476
buffer_tank_1000l_chf_installed: 4000   # estimate
site_plumbing_chf_low: 5000        # estimate
site_plumbing_chf_high: 15000      # estimate
# C opex
elec_basel_iwb_h4_2026_rp_per_kwh: 33.25
elec_basel_iwb_c2_2026_rp_per_kwh: 32.745
elec_basel_iwb_c3_2026_rp_per_kwh: 32.427
server_hw_incident_rate_per_year: 0.08
hdd_afr_2025: 0.0136
maintenance_pct_capex_per_year: 0.10    # planning value (3rd-party 8-15%, OEM ~20%)
server_life_years_planning: 5
server_life_years_hyperscaler: 6
ch_tax_writeoff_it_years: 5
# D heating comparison
heat_pump_air_water_install_chf_low: 45000
heat_pump_air_water_install_chf_high: 60000
heat_pump_ground_install_chf_low: 55000
heat_pump_ground_install_chf_high: 80000
bs_subsidy_air_water_base_chf: 8000
bs_subsidy_air_water_per_kwth_chf: 250
bs_subsidy_max_share: 0.40
heat_pump_running_cost_chf_per_year_low: 1000
heat_pump_running_cost_chf_per_year_high: 1600
oil_heating_cost_chf_per_year: 4000
heating_oil_chf_per_100l_sep2026: 160
heat_pump_spf_ch_air_water_measured: 3.19
heat_pump_spf_ch_ground_measured: 4.26
heat_pump_spf_case_assumption: 2.5
```

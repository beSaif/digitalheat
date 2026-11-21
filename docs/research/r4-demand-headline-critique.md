# Round 4 critique: demand side and the headline run

Critic for [r4-demand-headline.md](r4-demand-headline.md). Role: a sceptical DigitalHeat founder. Written Sat 21 Nov 2026. Plans and assesses only; no file of the investigator was changed.

**Tools:** WebFetch (4 pages) and local Python. **Firecrawl calls used: 0 of 1.** Currency CHF, 1 USD = 0.8392 CHF (inherited from round 1, ECB 20 Nov 2026).

## 1. What I re-ran

| Check | Result |
|---|---|
| `python3 analysis/r4_headline.py` (36 s wall, 186 s CPU) | Output **identical** line for line to the one pasted in the investigator's file, section (c), including the section 0 regression `all regression checks: OK` |
| Both inline commands in section (b) (shaped120/150; 2025-01-13 idle permits) | Reproduced exactly: N=6 120% 76.46% / 81.7% / 0 of 32,586; 150% 78.23% / 64.0%; N=8 120% 89.72% / 82.8% / **12 of 38,748**; 150% 91.80% / 65.4% / **13 of 38,325**; idle permit hours 22 (N=6) and 16 (N=8) |
| `analysis/r4_offers_shaped100_seed1.csv` | 8,760 rows; total offers 33,676 (N=6) and 39,244 (N=8), equal to the stated totals |
| Hand checks on the headline | Electricity 28,761 h x 1 kW x 0.3325 = 9,563 CHF. Heat used 3,060 / 0.133 = 23,008 kWh = 0.8 x 28,761, so all server heat is used. Coverage 23,008 / 31,231 = 73.67%. Utilisation 28,761 / (6 x 8,760) = 54.7%. All consistent with the case formulas |

## 2. Web sources (all opened with WebFetch on 21 Nov 2026)

| Claim | Found on the page | Verdict |
|---|---|---|
| c1 SRF 1.25 M hours of spoken content | "gut eineinviertel Millionen Stunden gesprochene Inhalte, viele davon auf Schweizerdeutsch", 22.01.2023. **The same article says SRF already has certain archive content transcribed automatically** by Recapp's system ("kann SRF bestimmte Archivinhalte heute automatisch verschriftlichen lassen"). | survives with caveat: much is Swiss German and part is already served by an existing ASR supplier |
| c2 SRF > 1 M hours of audio + 250,000 h video | "Über eine Million Stunden Audio- und rund 250'000 Stunden Videomaterial lagern im Keller des SRF in Zürich", 27.03.2024. The article also describes music holdings; it does not split audio into speech and music. | survives with caveat: not all of it is transcribable speech |
| c3 1.5 M inpatient stays, 23.9 M outpatient consultations, 2023 | quoted exactly, published 26 Nov 2024 | survives |
| c4 Suva 2.7 M invoices in 2024 | "2,7 Millionen Arzt- und Spitalrechnungen hat die Suva im letzten Jahr erhalten und geprüft", page dated 24 Sep 2025 | survives |

## 3. Findings that break or bend the result

### F1. The N=8 recommendation is an artefact of scaling demand with the number of servers (c29, plan change 6): rejected

`shaped100` sets the contract to each N's *own* expected heat capacity: 92 jobs a day at N=6, 108 at N=8. So "N=8 covers 12.5 points more" also assumes **17% more paying customers** for a bigger fleet. The investigator's own section (a) concludes that demand, not heat, is what binds. So I ran both N under the *same* contract (*computed*, scratchpad probe that monkeypatches `r2_deadline_sim.offer_rates` and calls `r4_headline.run` with the headline policy, seeds 1–3):

```
N  demand             cover   util   acc%   sumJ1%  missed(seed1)    sold_h  J1sold_h  BE     BE+rst  inc_c   starts offered/d
6  fix8_shaped100     74.99%  55.7%  81.6%   90.3%  0 of  31663    29,274   14,054 0.2261 0.2274  54,368    655  108.0
8  fix6_shaped100     73.88%  41.2%  94.7%   89.6%  0 of  31933    28,842   14,102 0.2261 0.2320  53,754   2944   92.2
6  flat               53.67%  39.9%  64.1%    0.0%  0 of  21650    20,952    9,335 0.2261 0.2334  38,382   2632   92.3
8  flat               60.48%  33.7%  62.4%    0.0%  0 of  24658    23,612   10,688 0.2261 0.2338  43,379   3102  108.1
```

(fix6_ = N=6's contract, fix8_ = N=8's contract; flat = r2's `flat`, the same yearly volume offered evenly every day.)

- With N=6's contract, **N=8 covers 73.88% against N=6's 73.67% (+0.2 points)**. Utilisation falls to 41.2%, starts go from 854 to 2,944 a year, and break-even with the restart line rises from 0.2278 to 0.2320 CHF.
- With N=8's contract, N=6 covers 74.99%, more than N=8 does with N=6's contract.
- So **under a fixed demand, N barely moves coverage.** The +12.5 points exist only if the extra two servers bring their own customers. The 6-vs-8 choice depends on a question nobody can answer yet: does demand grow with installed servers? The recommendation does not survive as worded.

### F2. The headline is heat-shaped by assumption; a flat customer gives 54% / 60% (c10, plan changes 1, 2 and 5)

`shaped100` assumes a buyer who sends 144 J1 + 18 J2 jobs a day in January and 15 + 2 in July: a **9.6 : 1 winter-to-summer swing**, exactly matched to the house's heat. Every customer the investigator found looks different. An archive is a deadline-free backlog. Hospital and insurer documents arrive roughly flat through the year. The same yearly volume offered **flat** gives coverage **53.7% (N=6) / 60.5% (N=8)**, 62–64% of jobs accepted, and **0% of summer J1** again (table above). This is the "does not pay off when" line the plan is missing: the headline needs customers whose demand moves with the weather. It is a bigger effect than the half-rate row.

Also, `shaped100` is "offers = our own expected capacity". The 95% acceptance and the 92.6% "sold share" follow from that choice by construction. The number is finite and reproducible, which satisfies the must-have's "say where it comes from". It is not evidence of demand, and the pitch must not imply that it is.

### F3. The income line sells 7.5 SRF archives per house per year (c18, plan change 7)

Under the headline, N=6 sells 14,101 J1 server-hours a year. At 667 audio-hours per server-hour that is **9.4 million audio-hours a year from one house**, about 7.5 times SRF's whole spoken archive (a one-off stock), every year, per house (*computed* from the investigator's figures). Section (a) of the same file shows that no named Swiss customer comes near this. The 53.6k CHF scenario is therefore income at a demand the document itself shows does not exist among named buyers. It rose from round 3's 39k only because the 67% sold-share assumption was replaced by a contract we chose to size at 100% of capacity. Keep it as a labelled scenario ("at contract = 100% of normal heat capacity"). Do not let it read as an improvement found in the data.

### F4. The pinned real job: the demo-day form is consistent, but two gaps remain (c25, c26, plan change 4)

- "Same pattern with and without the pin" is close to true by construction: the pinned job runs whenever k >= s, and the no-pin pattern is also k >= s. The pin can only change the pattern through its small effect on the tank. It is a weak check, not evidence.
- The balance books 8 h (N=6) or 19 h (N=8) of 1 kW J1 work, about 5,300 to 12,700 audio-hours, for a live process that transcribes a few minutes of audio on the laptop. The README must say that the live process stands for slot s's work on that day; it does not perform all of it. The audio set must also last past the RESUME in a 1.5 s-per-hour replay, or there is nothing to resume.
- The all-year finding (c24) holds: an always-ready backlog on slot 1 is 22–26% of sold hours and brings summer J1 back to 0%.

### F5. Smaller points

- c15 "92.6% of the unlimited-demand permit hours": the denominator (31,067) is plain follow *without* cap + band. Against the headline policy's own saturating hours (30,925) the share is 93.0%. Rounding-level, but it compares two different policies.
- c27 leaves out that misses come back at N=8 at 120% and 150% offers (12 and 13 a year); the investigator's file does print them.
- The 0 missed depends on the archived forecast being from the same model family as the "truth" and on restart staying out of execution. Both are disclosed; keep the stress line next to it.
- c5–c7 set one-off stocks (archive) against an annual house capacity. The comparison is labelled, but "6% of a house-year" is a once-only figure, not a yearly demand.

## 4. Verdict summary

Claims: c1, c2 survive with caveat; c3, c4 survive; c5–c8 survive (c5 and c6 with caveats); c9, c11–c14, c16, c17, c19–c24, c27, c28, c30 survive; c10, c15, c18, c25, c26 survive with caveat; **c29 rejected** (F1).

Plan changes: 1 accept_modified (add the heat-shaped label and the flat line); 2 accept_modified; 3 accept; 4 accept_modified (live slice wording); 5 accept_modified (flat contract as the "does not pay off" line); **6 reject**; 7 accept_modified; 8 accept; 9 accept, with one more question.

## 5. Questions a founder would still ask

1. Who signs a contract that is ten times bigger in January than in July? Name one batch-compute buyer whose demand follows Basel's weather.
2. If demand is what binds (your own conclusion), why buy two more servers? Under the same demand N=8 adds 0.2 points of coverage and triples the starts.
3. Your income line sells 9.4 million audio-hours a year from one house. Who are those customers, and how does the audio get into a basement (network and storage)?
4. SRF already has archive content transcribed by an ASR supplier, and much of it is Swiss German. Why would it send that work to Whisper on distributed basements?
5. What happens to the 5% of refused jobs: who is the partner site, and does the customer pay for a job that is moved?
6. With a flat customer, coverage is 54% and summer J1 acceptance is 0% again. Which is your realistic case?

Scratchpad probe and outputs (temporary): `/private/tmp/claude-502/-Users-saif-Work-digitalheat/54033c20-c34b-4790-8603-f4e497e39cb8/scratchpad/r4demand_critic_probe.py`, `.../r4demand_critic_rerun.txt`, `.../r4demand_critic_inline.txt`.

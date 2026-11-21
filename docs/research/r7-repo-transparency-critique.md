# Round 7 critique: repository reproducibility and the transparency package

Critic, Sat 21 Nov 2026. I took the role of a sceptical DigitalHeat founder. I reviewed [r7-repo-transparency.md](r7-repo-transparency.md), [r7-real-vs-analysis.md](r7-real-vs-analysis.md), `analysis/r7_critic_probes.py` and `analysis/r7_econ_bridge.py`.

Ground rules for this review:
- **Assessment only.** I changed no git state. The only git commands I ran were `git ls-files`, `git check-ignore` and `git archive HEAD`; the archive went into the scratchpad. I edited no existing file.
- **Web.** Two free WebFetch calls and no Firecrawl calls.
- **Currency.** CHF throughout.

## 1. What I re-ran

I built my own clean copy in the scratchpad (folder `r7crit_repro/clone`) as follows:
1. `git archive HEAD`: 22 tracked files, and no `analysis/` folder.
2. Added exactly the 26 files from section 2: **26 files, 3,071,061 bytes**, which matches.
3. Ran every key command from the copy's root with `PYTHONDONTWRITEBYTECODE=1` and Python 3.13 (miniforge). `PYTHONPATH` was empty.

| Command (clean copy) | Exit | Notes |
|---|---|---|
| baseline_sweep, one_rack_model (default and `--sold 1.0`), r2_fleet_economics, r2_realism, r4_machine, r4_tank_layout, r5_chain, r6_machine, r6_build_scope `--loc-only`, r7_econ_bridge, r6_buyer_scenarios, r6_build_scope, r7_critic_probes, r4_headline, r5_pitch_numbers, r3_policy_check | 0 | Byte-identical to a run in the repo for baseline, r5_chain, r6_machine, r7_econ_bridge, r6_buyer_scenarios, r7_critic_probes, r2_fleet_economics and r4_tank_layout. I did not byte-compare the rest; their quoted figures appear unchanged. |
| r5_pitch_numbers | 0 | 154 MATCH, 2 DIFF (I6, I9), as claimed |
| r6_build_scope section 5 | 0 | "byte-identical … True" |
| r6_build_scope `--loc-only` with `pause_resume_probe.py` removed | **1** | `FileNotFoundError`, as claimed (c4) |
| `analysis/fleet_scenario.py` (team file, new at 12:00) | **1** | `FileNotFoundError: data/raw/basel_wohnviertel.geojson`. That geojson file is untracked. |
| r7_payback.py (parallel agent) | 0 | |
| Fast scripts under macOS `/usr/bin/python3` 3.9.6 | 0 | Output identical. The README's "3.10+" is safe but stricter than needed. |

Two long-running commands, also run in the clean copy:
- `r5_miss_stress.py`: exit 0, 150 s. It prints the quoted stress figures: overrun 0.389% / 0.240%, and −1 K at most 18 a year at N=8.
- `r2_deadline_sim.py`: exit 1, `FileNotFoundError` for `prev_runs_basel_2025.csv`, as claimed (c5). I did not re-run it with that CSV added.

**Sources I opened myself:**
- **ECB reference rates**, <https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml>: dated 2026-11-20, USD 1.0990 and CHF 0.9223 per EUR. That gives 0.9223 / 1.0990 = **0.8392 CHF per USD**, so c20 is confirmed.
- **PNY / NVIDIA RTX PRO 6000 Server Edition brief**, <https://www.pny.com/en-eu/file%20library/professional/rtx-pro-6000-server-product-brief.pdf>. I extracted the text with `pdftotext -layout` and it reads: "Uncontrolled environment:1 864,500 hours at 35 °C / Controlled environment:2 1,062,500 hours at 35 °C". The note under it reads: "1 Some environmental stress with limited maintenance (GF35)". So the "1" is a footnote marker, and the round-6 correction to 864,500 h (1.01% per year) holds.

## 2. Findings, most serious first

### F1. "Every figure in Read this first" is not reprinted: at least one live Q&A figure has no saved command

Q&A 7 in "Read this first" quotes "3,198 / 5,346 permit server-hours a year with no admitted work":
- It comes from an "inline check in this session" (r5-missed-deadline-robustness.md line 97; round-5 critique c15).
- No saved script prints it.
- `r7_critic_probes.py` does not include it, and the investigator's "estimate" list does not name it.

It is computable: `sum(ks_cap − ks_on)` from `r4_headline.run(n, HEADLINE, 'shaped100', 1)` gives 3,198 and 5,346. I checked this with a one-off command and saved nothing under `analysis/`.

So the claim "a fresh clone can reprint every figure quoted in Read this first" is **overstated**. A complete audit would need to grep every number in "Read this first" against the clean-copy outputs. That audit was not done; the investigator listed figures by memory of the critiques.

Fix: add the two lines to `r7_critic_probes.py` (5 minutes), or label the figure "estimate".

### F2. The README text links files that the "minimal" set leaves out

- **Docs.** The proposed README block points to `docs/research/r2-missed-deadlines.md` and `r5-missed-deadline-robustness.md` for the Open-Meteo URLs. The real-vs-analysis table points to r6/r7 research files. None of these is in the 26-file set; the docs are listed only as "optional". A juror who clicks these links gets a 404. The set is minimal for *running*, not for the README as written.
- **Personal path.** Committing `docs/research/` brings in the local home path, including the account user name. That path is now in **five** files: the four listed plus `r7-scheduler-forecast-critique.md`, written this round by a parallel agent.

Decide one of these:
- (a) commit the docs and accept the path; or
- (b) copy the two Open-Meteo URLs into the README itself and do not link `docs/research/`.

(b) is simpler.

### F3. `git add analysis/` (the "simplest team action") breaks the team's own new dashboard script

`analysis/fleet_scenario.py` was written by the team at 12:00 to make the dashboard inputs. It reads `data/raw/basel_wohnviertel.geojson`: 329,065 B, untracked, CC BY 4.0, so it needs attribution. After `git add analysis/` it fails in a clone (tested above).

Other notes on this option:
- The folder is **3.64 MB** without `__pycache__`, not "about 4.2 MB".
- It also brings in `r7_forecast_paths.py` and `r7_payback.py`, which this round did not test. I tested `r7_payback.py` and it runs (exit 0).

Fix: `git add analysis/ data/raw/basel_wohnviertel.geojson`, then repeat the clone check.

### F4. The 14:15 "fresh clone" check is not a fresh clone unless someone pushes

The check, as written ("run `git clone` into a fresh folder"), would clone the local repo. That only tests what was committed, not what the jury sees. The test that counts is to clone the remote after a push.

Pushing is a team action, outside this loop. But the plan should say "after a push, clone from the remote URL", or the check proves less than it claims.

### F5. The one-number economics choice rests partly on a weak reason

The recommendation (reference-server basis in the README and pitch, `one_rack_model.py` as a sensitivity) is defensible. The investigator gives three reasons, and one of them does not hold.

- **Reason 1 holds.** The basis must be consistent with must-have 1: J1/J2 sizing and work per kWh come from MLPerf rows on the reference server. Consumer RTX 4090s have no MLPerf datacenter row in our data. Pricing work from one machine against the capital cost of another would be the worse mix.
- **Reason 3 is weak.** "Its installed cost includes the house side" is not a real difference. I decomposed `r5_chain.installed(6, 'DLC')` (computed, a one-off command in the scratchpad):
  - servers: 6.284 boxes × 30,026 = **188,700 CHF** (89%);
  - house side: 23,874 CHF (house integration 14,788 + buffer 1,167 + CDU 3,000 + fresh-water station 2,000 + DHW cylinder 2,919);
  - one_rack at N=6 already carries 6 × 3,000 = 18,000 CHF of install. That is the same order of magnitude.

  The real gap is **GPU hardware**: about 31,450 CHF per server slot (new RTX PRO 4500 at 4,819 CHF each × 4, plus an 8,000 CHF platform, plus cold plates) against 5,924 CHF for a used 2 × RTX 4090 rig. That is a factor of about 5.3, not "4.0 incl. house". This is a business choice: question 1 of the "five questions for DigitalHeat". It is not a modelling error in either file.

What the pitch should say, if asked: "price needed per sold server-hour is about 0.63 CHF with used consumer cards and about 1.6–1.7 CHF with new datacenter cards on cold plates. Neither has a buyer we found."
- Both values are computed, by `r7_econ_bridge.py` steps 5 and 7 and by `r6_buyer_scenarios.py`.
- This is more honest than hiding one_rack as a footnote.
- It still never puts one_rack's 0.2826 next to 0.2261.

Unverified point, not checked this round: whether NVIDIA's GeForce driver licence allows this kind of deployment. A founder would ask about it before backing the consumer-GPU path.

### F6. The bridge is called "7 single-input steps", but it is not

- Step 5 changes N, capital cost and opex at once.
- The end point, 1.595 CHF, is the bridge's own follow-policy construction. No basis-2 script prints it; `r6_buyer_scenarios` "pool" prints 1.601.
- The attribution depends on the order of the steps. Hardware is still the largest step in any order I checked: done at N=1 it adds (35,429 − 8,924) / 5 / 7,629 = 0.695 CHF per hour, against 0.07–0.19 for every other step.

The conclusion stands; the wording should be "7 steps (step 5 changes three inputs)".

### F7. `r5_pitch_numbers.py` is a poor README command for a jury

- It prints "MATCH/DIFF" against "plan" values hard-coded from the round-4 state of `docs/overnight.md`, an internal file that may never be committed.
- It ends by printing two DIFF lines (I6, I9).
- A juror reads "DIFF" as an inconsistency in the submission.

Either drop it from the README block or describe it as "reprints the round-4 figures; DIFF = rounding difference against an earlier draft". The direct scripts (`r4_headline`, `r6_build_scope`, `r7_critic_probes`) already cover the slide figures.

### F8. Small wording mismatches that remain in "Read this first" (not introduced by the investigator, not flagged either)

- Item 9 says "about 12–15% incl. maintenance and card failures on the liquid configuration". `r7_critic_probes.py` E prints 13.4% / 14.6% for that configuration, so "about 13–15%". The 12% end is the reference server or the unsaved 3 h-service variant.
- Q&A 1 says "8–10% over 8" for the RTX PRO 6000 configuration. E prints 9.4% / 10.1%, so "about 9–10%".
- The r7 table states both correctly; the plan text should follow it.

### F9. Card failure rate: verified, but applied to both cards

I verified the MTBF. `r7_critic_probes.py` E applies the RTX PRO 6000 SE figure to the RTX PRO 4500 as well. The r6_machine comment already calls this an *assumption*. The figure is also a 35 °C prediction; the round-6 critic says to treat it as a floor. Keep both caveats on the 11.8% / 12.9% row.

## 3. What survives

The core result holds:
- With the 26 files committed, a clone runs every key script offline with the standard library.
- The offer CSV regenerates byte-identical.
- The saved probes reprint the round-5 and round-6 critic figures exactly.
- one_rack's 0.2826 is indeed 0.2261 / 0.80.

The corrected table fixes the round-6 faults (stages, no-guard, not-told, offer CSV).

None of this adds build scope. Committing is a few minutes of team time; F1, F2 and F7 are each under 10 minutes.

## 4. Questions a DigitalHeat founder would still ask

1. The authority for every slide figure is "the team scheduler's printout", but no scheduler code is in the repo yet. What exactly can a juror run today that is *your* scheduler and not an analysis mirror?
2. 213,000 CHF of hardware in one family house, for 6 kW of compute: who finances that, and why would a homeowner host it? With used consumer cards it is about 54,000 CHF (6 × 8,924); why not pitch that?
3. In "not told" outages, the scheduler keeps admitting work to a house that is dark. How does the real system detect a house that has gone dark (heartbeat, power meter), and how long does that take?
4. Every figure is for a stand-in reference house. If the official CSV arrives Saturday afternoon, which figures change, and does the regression oracle still apply?
5. The 864,500 h MTBF is NVIDIA's prediction for one card at 35 °C air. Your cards sit on cold plates in a basement, with retrofit plates that void the warranty. What failure rate do you actually budget, and who pays for a dead card in year 4?

# Where the case assumptions stop holding

The case simplifies the physics so every team works from the same numbers. We keep those simplifications for the reference-house key figures, but we **must** say where they stop holding, in the implementation and in the pitch. The Feasibility criterion (25% of the score) rewards exactly this: "The solution knows where its assumptions stop holding and says when the model does not pay off."

> **Status of the numbers below:** general engineering ranges, not yet backed by a cited source. Before they go into the pitch or the repo README, check each one against the source named in its "Verify" line.

## 1. "Heat storage: no losses"

**Case says:** one 1,000-litre tank, 35 kWh usable (30 K spread), no losses.

**Reality:** a well-insulated tank of this size at around 60 °C loses roughly **2–4 kWh per day** to its surroundings.

| Season | Daily demand | Tank loss as share of demand | Effect of ignoring it |
|---|---|---|---|
| Winter | ~100–250 kWh (space heating + hot water) | ~1–4% | Negligible. The tank sits in the building, so the loss partly heats the basement anyway. |
| Summer | 12 kWh (hot water only) | ~15–30% | Significant. The loss is wasted heat, so summer coverage and heat-dumped figures look better than reality. |

**Verify:** standby-loss figures on EU energy labels (ErP, Regulation 812/2013) for 1,000 L storage tanks.

## 2. "Recovered heat can be used without a heat pump"

**Case says:** recovered server heat can go straight into space heating and hot water. DigitalHeat's slides target 50–70 °C.

**Reality:** it depends on how the servers are cooled and what the house needs.

| Server cooling | Typical outlet temperature |
|---|---|
| Air-cooled (fans) | ~35–45 °C air: too cold for hot water |
| Direct liquid cooling (cold plates) | ~45–60 °C water: usable; 70 °C is hard because chips tolerate limited coolant temperatures |

| House needs | Supply temperature | Server heat directly usable? |
|---|---|---|
| Underfloor heating (modern house) | ~30–40 °C | Yes, easily |
| Radiators (older house) | ~55–70 °C | Borderline |
| Domestic hot water | ≥60 °C in storage (Legionella prevention) | At the edge; a real system likely needs a small heat pump or electric top-up |

**Consequence:** for hot water and for older houses, a real installation adds a booster heat pump or an electric heater. That costs electricity and money the reference model does not count, so the model is optimistic exactly in summer (hot water only) and in older buildings.

**Verify:** Swiss hot-water hygiene guidance (SIA 385/1, BAG/BLV Legionella recommendations); ASHRAE liquid-cooling classes (W32–W45, W+) and vendor data for warm-water-cooled servers.

## 3. Our own modelling choice: hot water spread evenly

**Case says:** 12 kWh of hot water per day, no hourly pattern.

**We chose:** 0.5 kWh every hour (see [data/README.md](../data/README.md#reference-house-profile)).

**Reality:** use peaks in the morning and evening. Because hot water is drawn from the 35 kWh tank (about three days of hot water), the timing mostly doesn't matter. The exception is cold winter mornings when space heating already takes all the server heat and the tank is low: a shower peak then falls to the backup heater.

**Check once the model exists:** run the year with an even pattern and with a peaked pattern, and report whether the key figures change.

## How to use this

**Implementation**
- Keep the case simplifications as the default for the reference-house figures (comparability with other teams).
- Make each limit a switch or parameter that can be turned on: tank standby loss in kWh/day, a booster for hot water (COP or electric), the hot-water profile shape.
- Report the key figures twice: "case assumptions" and "with realistic losses and booster", and show the difference.

**Pitch**
- After the key figures, one slide or sentence: "These numbers use the case's simplifications. With tank losses and a hot-water booster, summer coverage drops by X and the break-even price rises by Y."
- Say plainly in which situations the model does not pay off (summer-only demand, old radiator houses, air-cooled servers).

# Live pitch script: DigitalHeat, Ctrl+Free

**Slot:** 5 min pitch with live demo, then 3 min Q&A. Sun 22 Nov, Pitch 2, room 2.22.
**Story in one line:** computing jobs go only where a building needs heat, and when a tank is full the work moves on without starting over.

## Roles

| Who | Does |
|---|---|
| **Speaker** | Talks. Faces the jury, never the laptop. |
| **Operator** | Drives `/live` on the projector laptop. Clicks on the cue, says nothing. |
| **Lena's phone** | A team phone already joined as "Lena" (the house). Held up when the script says so. |
| **Customer** | A laptop or phone with `/client` open, handed to the jury. If they don't want to take it, the Speaker orders. |

## Before you walk in (10 min)

1. `pnpm build && pnpm start` on the operator laptop. Start the tunnel if the venue Wi-Fi keeps devices apart (see the dashboard README).
2. Open `/live` on the projector. Press **Reset**.
3. Join the team phones, in this order, so the building types line up: **Lena** (house), **Anna** (pharma lab), then the others (family home, spa…). Keep every phone screen on.
4. Pick **January**. Check that Lena's row says "needs … kW" and her tank is between 40 and 80 %.
5. Order one test render, let it finish, then press **Reset** and rejoin the phones (or leave the finished job in the list: it doesn't hurt).
6. Open `/client` on the customer laptop. Choose 3D rendering, but don't press Order.
7. Have the demo video open in a tab, ready to play. **If the live demo breaks, play it and keep talking.**

## The script (5:00)

Spoken lines are in quotes. **[Cue]** = what the operator does. Times are where you should be.

### 0:00 · The problem

> "Servers turn almost all the electricity they use into heat, and data centres pay again to cool it away. Meanwhile every building in Basel pays to make heat. DigitalHeat puts the servers in the basement. The open question they gave us was: which jobs, scheduled how, and does it pay?"

> "We built the scheduler that answers that, and we'll show it running on the phones in this room."

### 0:30 · The fleet

**[Cue]** Projector on `/live`, January selected.

> "This is DigitalHeat's control screen. January, eight in the morning, Basel. Every one of these buildings has a rack of servers, enough to cover all of its heat. No heat pump, no backup heater."

**[Cue]** Hover over **Lena's** pin on the map. On the card, click **3D view**.

> "This is Lena's house. Her phone is standing in for her fourteen servers."

Hold Lena's phone up for a second.

**[Cue]** Click **Back to map**.

### 1:00 · The customer orders

Hand the customer laptop to the jury.

> "You're the customer. You want a 3D image rendered. You see the price before you order, and you never see a server. Go ahead and press Order."

**[Cue]** If the jury doesn't press it, the Speaker presses **Order**.

> "The image is cut into sixty parts. The scheduler only gives parts to buildings that need heat right now, and on a January morning that's all of them."

**[Cue]** Point at the **Rendered by** row under the image. Hover **Lena** in that row: her parts light up.

> "Each colour is one building. Every part with Lena's colour was rendered in her basement, and that heat went into her tank, not into a cooling tower."

### 2:00 · The tank fills up

> "Now the interesting case. What happens when Lena's tank is full?"

**[Cue]** Hover Lena's pin. Wait until the card says **Working on part …** (her rack rests between parts), then click **Fill tank**.

> "Her tank is at a hundred percent. She doesn't need more heat, so her rack stops. She was halfway through a part."

Point at that part in the image: it shows **saving**, then a percentage.

> "Her phone saves where it got to. That part continues on Anna's pharma lab, which still needs heat, from that percentage. Nothing is computed twice."

**[Cue]** Point at the dashed arrow on the map from Lena's house to the pharma lab. Hold Lena's phone up: it says **Tank full · paused** and where the part went.

> "That's exactly what DigitalHeat asked for: jobs that can slow down, pause, and move. When her tank has cooled to ninety percent, her rack comes back on by itself."

### 3:00 · Summer

**[Cue]** Click **July**. On the customer laptop, choose **AI reranking**, pick the aspirin question, then **Order**.

> "Same fleet, July, two in the afternoon. The customer now asks an AI to search five thousand scientific abstracts for a claim."

> "Homes only need hot water now. Lena runs one or two of her fourteen servers. The work goes to the pharma lab and the spa, which need heat all year. Less heat needed means less computing, and the scheduler follows it."

**[Cue]** Point at the best matches as they appear.

> "These are real AI models, the same ones we measured, running on phones in this room."

### 3:45 · Does it pay?

> "We ran the same scheduler over a full year of Basel weather for the case's reference house with four servers."

Say the numbers slowly:

> "It covers 58 % of the house's heat and never throws heat away. The servers are busy 65 % of the time, and not one of 27,000 jobs missed its deadline."

> "It breaks even at 1.11 francs per server-hour, hardware included. Sold at the AWS spot price, 2.74, that one house earns DigitalHeat about 37,000 francs a year. It stops paying off below 23 % utilisation."

### 4:30 · What's real, what's next

> "What's real: the scheduler, the AI jobs, the rendering, and the pause, checkpoint and move, which also works on a real running job on our laptops. What's simulated: the tanks. They run sixty times faster so you can see the heat."

> "With four more weeks we'd put one real server and tank in a Basel building, plan from the weather forecast, and sign two pilot customers whose data has to stay in Switzerland."

> "Compute where the heat is needed. Thank you."

## If something goes wrong

| Problem | Do this |
|---|---|
| Phones won't connect | Say "the venue Wi-Fi keeps devices apart, here's the recording" and play the demo video from 0:00. Keep the script going over it. |
| The render is slow | Keep talking. The image doesn't have to finish. Move on to the tank part at 2:00 anyway. |
| Fill tank: nothing is saved | Lena was between parts (the card said so). Say "she was between parts, so nothing needed saving", then fill Anna's pharma lab: it works almost all the time, so it always holds a part. |
| A phone drops | It's a feature: "Lena just locked her phone, and her part went straight back to the queue." |
| Running out of time | Skip Summer (3:00) and go straight to the numbers. |

## Q&A: short answers

**Where does 50–70 °C come from without a heat pump?**
DigitalHeat's cold-plate loop. We used their 0.8 kW of heat per 1 kW server and haven't verified the outlet temperature. That's our first question for them.

**Why would a customer pay more than AWS?**
The data stays in Switzerland, in known buildings, and the price includes redundancy on capacity that's running for heat anyway. We price at AWS plus 25 %.

**What about summer, when nobody needs heat?**
Homes drop to hot water only, and the work moves to sites with heat all year: pharma, hospitals, spas. Utilisation falls to about a third from April to September. That's in the business case and it still breaks even.

**What if every tank is full?**
Jobs wait in the queue. Deadline jobs (reranking, due in 4 hours) go first to the building with the most free heat. Over the year: zero missed deadlines.

**Is the pause real or only in the demo?**
Both. `python3 -m scheduler.live` pauses, checkpoints and resumes a real embedding job on a laptop, using the same code as the yearly balance.

**Who pays for the electricity?**
The host's meter pays all of it, and DigitalHeat refunds the share the heat doesn't cover. The host pays for heat below the price of a heat pump.

**How many servers per house?**
The case's reference house has 4, and that's what the yearly numbers use. In the live demo every building has enough for 100 % of its heat (Lena's house: 14), because DigitalHeat said there's no heat pump and no backup.

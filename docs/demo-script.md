# Live demo script: from the house to the fleet

**Where it sits:** deck slide 5, "Live demo", between "Result" ("Now, the live demo.") and "Costs"
("Useful heat, useful work. But does it pay?"). The deck budgets **90 s** for it and the whole pitch runs
4:27, so you have about 30 s spare. Aim for 1:30; never go past 1:50.

**The case asks for exactly three things in the demo** (case brief, "Key presentation elements"):

| # | Case scenario | Where you show it |
|---|---|---|
| 1 | One January day | Live app, **January** (15 Jan, 08:00, −2 °C) |
| 2 | One July day | Live app, **July** (15 Jul, 14:00, 25 °C) |
| 3 | One interrupted job, on a real running process that the scheduler pauses and resumes on the heat signal | **Fill tank** in the live app (the part pauses, saves and moves), then the **terminal**: the same scheduler pausing and resuming a real AI job on this laptop |

The story runs from the house out to the fleet: one house in 3D first, then the map with the hospital and the spa,
then summer, when the work follows the heat out of the house.

## Numbers you'll see (scheduler output, `python3 -m scheduler.day`, sizing "tank")

Read them off the screen; these are what it should say.

| | House (11 servers) | Hospital (38) | Spa & pool (33) |
|---|---|---|---|
| **15 Jan, 08:00, −2 °C** | needs 9.1 kW · **11** running | 38 kW · **38** running | 21 kW · **26** running |
| **15 Jul, 14:00, 25 °C** | 0.5 kW (hot water) · **1** running | 14 kW · **17** running | 19 kW · **24** running |

Heat dumped: 0 at every site, both moments.

The live app gives every building the fewest servers that, with its tank, cover all of its heat for the year
(DigitalHeat: no heat pump, no backup), so the house has **11**: the same 11 as the deck's yearly figures.
If anyone asks why not 14 for the coldest hour, see Q&A below.

## Before you walk in (10 min)

1. **Fix the real job first. It crashes right now:** the `python3` on this laptop is missing pyarrow, torch and
   sentence-transformers (`runs/live/job.log`). Install `requirements-workloads.txt` in a `.venv` and rehearse
   the terminal step below until you see `start`, `pause (SIGSTOP)` and `resume (SIGCONT)`.
2. Dashboard: `pnpm build && pnpm start` (the production server on :3000 is an old build without `/pitch`).
3. **Tab 1:** the deck, `/pitch`, on slide 1, full screen.
4. **Tab 2:** the live app, `/`. Press **Reset**, pick **January**. Check the moment pill says
   `08:00 · 15 Jan · -2 °C` and "3 of 3 buildings need heat".
5. **Customer laptop or teammate's phone:** `/client`, **3D rendering** selected, Order not pressed yet.
6. **Terminal**, font large, command typed but not run:
   ```bash
   .venv/bin/python -m scheduler.live --seconds-per-hour 3 --hours 14 \
     --sites-json '[{"id":"BS-01","kind":"house","name":"Reference house","lat":47.56,"lon":7.59,"servers":11}]'
   ```
   It plays server 1 of the 11-server reference house on 15 July from 06:00. Fast-forwarding to July takes a
   while before the first line, so **start it when you reach slide 4** ("Result"). By the time you need it, it's
   pausing and resuming every 3 to 6 seconds.
7. The demo video open in another tab. If the live demo breaks, play it and keep talking.

## The script (1:30)

Spoken lines are quoted. **[Cue]** = what you click.

### 0:00 · January, the house

**[Cue]** Switch to tab 2 (January already on). Click the **House** pin, then **3D view**.

> "This is the reference house in Basel. 15 January, eight in the morning, minus two degrees.
> It needs nine kilowatts of heat right now."

> "Its basement has eleven servers, and all eleven are on. The cold night has emptied the tank,
> so the house takes every bit of their heat. Not one kilowatt-hour goes to waste."

### 0:20 · Out to the fleet

**[Cue]** Click **Back to map**. Nod to the customer: they press **Order** on `/client`.

> "The same scheduler runs the whole fleet: this house, a hospital, a spa. At minus two, everyone wants heat."

> "A customer just ordered a 3D render. It's cut into sixty parts, and the parts only go to buildings that need heat.
> Each colour is one building."

**[Cue]** Point at the parts filling in.

### 0:40 · The interrupted job

**[Cue]** Open the House card. Wait until it says **Working on part … now**, then click **Fill tank**.

> "Now the family stops drawing heat. The tank is full. Watch the house's part."

**[Cue]** Point at the part: *saving*, then a percentage, then the arrow on the map to another building.

> "The rack stops mid-part, saves exactly where it got to, and another building that still needs heat
> finishes it from there. Nothing is computed twice. When the tank cools to ninety percent,
> the house's rack switches itself back on."

### 1:00 · July: the work follows the heat

**[Cue]** Click **July**.

> "Same fleet, 15 July, two in the afternoon, twenty-five degrees. The house only needs hot water now:
> half a kilowatt, one server out of eleven. The hospital drops to seventeen.
> But the spa still heats its pool: twenty-four servers. The work goes where the heat is wanted."

### 1:15 · The real process

**[Cue]** Switch to the terminal (already running).

> "And it's not only on screen. This is the same scheduler code controlling a real AI job on this laptop,
> as one server of the reference house on that July day."

**[Cue]** Point at the lines as they come:

```
[t=4686] start: 1 of 11 servers have heat
[t=4687] pause (SIGSTOP): no heat this hour, heat again within 2 h
[t=4688] resume (SIGCONT): 1 of 11 servers have heat
```

> "No heat needed: it pauses. Heat needed again: it carries on from where it was.
> If the heat stays away longer than two hours, it saves a checkpoint and can restart on any server."

**[Cue]** Back to tab 1, next slide.

> "Useful heat, useful work. But does it pay?"

## What else to work in (the jury scores these)

Only if you have the seconds; each is one sentence.

- **Transparency (25 %):** "Every number on this screen has its source behind this button." (Click **Sources** once, close it.)
  "One command reruns the whole year."
- **Feasibility (25 %):** say what's simulated, before they ask: "The tanks run sixty times faster than real
  time so you can see the heat. The heat side is simulated; the scheduler, the jobs and the pause are real."
- **Scheduling quality (20 %):** the two numbers they weigh first are coverage and heat dumped.
  On the yearly run that's 99.97 % and zero. Say "zero dumped" out loud during the demo.
- **Creativity (20 %):** the move. A paused part doesn't just wait: it continues in another building
  from its last percentage.
- **Design (10 %):** "A homeowner sees one thing: is my house getting heat, yes or no." Point at the coloured
  ring on the house pin.

## If something goes wrong

| Problem | Do this |
|---|---|
| Live app won't load | Play the demo video, keep reading this script over it. |
| Fill tank: "Between parts" | Wait two seconds and click again, or fill the **Hospital**: it's almost always holding a part. |
| The render is slow | Don't wait. Move on to July at 1:00 anyway. |
| Terminal shows nothing yet | It's still fast-forwarding to July. Say "it's catching up to July", go back to the slides, and show it in Q&A. |
| Terminal shows "worker crashed" | The Python packages are missing (step 1 above). Skip the terminal, and say the Fill tank was the same pause. |
| Out of time | Cut the July step to one sentence. Never cut the interrupted job: it's a must-have. |

## Q&A: short answers about the demo

**Why 11 servers, when the coldest hour needs 14?**
The tank. It stores heat from the milder hours and hands it out in the coldest ones, so 11 servers cover every hour
of 2025 (99.97 %: the model starts 1 January with an empty tank, which costs 9 kWh on the first morning).
DigitalHeat told us there's no heat pump and no backup, so we didn't go lower: 10 servers cover only 99.3 %.
Sizing for the coldest hour alone would take 14, and three of them would sit idle almost all year.

**Is the pause real?**
Yes. The terminal is a real process: SIGSTOP pauses it, SIGCONT resumes it, and a longer break stops it at a checkpoint
it can restart from anywhere. It's the same Scheduler class that produces the yearly balance.

**What's simulated?**
The buildings' heat demand (case formula, Basel weather 2025) and the tanks. The jobs, the scheduler and the pausing are real.

**What if every tank in the fleet is full?**
The work waits in the queue. Deadline jobs go first to the building with the most room in its tank. Over the year: zero missed deadlines.

**Why does the spa stay busy in July?**
It heats a pool and a 30 °C hall all year. That's why the fleet mixes homes with sites that need heat in summer.

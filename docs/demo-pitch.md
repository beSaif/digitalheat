# Demo pitch: the website, for the jury (4 min)

**What this is:** a 4-minute spoken walkthrough of the live website, `/`, for a demo-only slot or a jury that
comes to the table. The 90 s version inside the deck is `docs/demo-script.md`. The full 5 min pitch with
slides is `docs/pitch-script.md`.

**The one idea to land:** the work goes where the heat is wanted, and when a building has enough heat
the work moves on without starting over.

**What's different here:** the jury takes part. They scan the QR code and their own phones become
servers in a Basel building. They order the job. They see their phone pause.

## Roles

| Who | Does |
|---|---|
| **Speaker** | Talks to the jury and points at the projector. Doesn't touch the laptop. |
| **Operator** | Drives `/` on the projector laptop. Clicks on the cue and says nothing. |
| **Customer** | A team laptop with `/client` open, handed to a jury member. |
| **Backup phones** | Two team phones already joined. If the jury won't scan, these are the fleet. |

## Before you walk in (10 min)

1. `cd dashboard && pnpm build && pnpm start`. Phones join on the laptop's address (the QR code shows it).
   If the venue Wi-Fi keeps devices apart, run `cloudflared tunnel --url http://localhost:3000` and open
   `/?join=https://….trycloudflare.com`, or use a phone hotspot. **Scan the QR code with a phone you haven't
   used yet to check it.**
2. On `/`, press **Reset** (the ↺ icon in Jobs), then pick **January**. The pill at the top should say
   `08:00 · 15 Jan · -2 °C` and "3 of 3 buildings need heat".
3. Join the two backup phones now, so the jury's phones become the third, fourth and later buildings.
   Keep their screens on (locking a phone takes its building offline).
4. On the customer laptop, open `/client` and select **3D rendering** › **Living room, evening**. Don't order yet.
5. Terminal, large font, typed but not run:
   ```bash
   .venv/bin/python -m scheduler.live --seconds-per-hour 3 --hours 14 \
     --sites-json '[{"id":"BS-01","kind":"house","name":"Reference house","lat":47.56,"lon":7.59,"servers":11}]'
   ```
   It takes a while to fast-forward to July, so **start it when you start talking**.
6. Have the demo video open in a tab. If the live demo breaks, play it and keep reading this script.

## Numbers you'll see

**Read the numbers off the screen.** Every tank starts a little below the scheduler's level, so the
server counts are not the same every time. These are the scheduler's own numbers (`scheduler.day`,
sizing "tank") for the three base buildings:

| | House (11 servers) | Hospital (38) | Spa & pool (33) |
|---|---|---|---|
| **15 Jan, 08:00, −2 °C** | needs 9.1 kW · **all 11 on** | 38 kW | 21 kW |
| **15 Jul, 14:00, 25 °C** | 0.5 kW (hot water) · **1 or 2 on** | 14 kW | 19 kW |

Heat dumped: zero everywhere, both moments. The jury's phones join as a house, then a pharma lab, a family
home, a spa, an office, a greenhouse and a city house, in the order they scan.

**A rack only counts servers while it's working on a customer's job.** Before the first order every rack
shows 0. That's why the order comes before the close-up of the house.

## The script (4:00)

Spoken lines are in quotes. **[Cue]** = what the operator does. The times show where you should be.

### 0:00 · What you're looking at

**[Cue]** Projector on `/`, January selected.

> "This is DigitalHeat's control screen. Every pin is a Basel building with servers in the basement.
> The fifteenth of January, eight in the morning, minus two degrees."

> "The servers don't run when there's computing to do. They run when a building needs heat.
> Let's put you in the fleet."

### 0:20 · The jury becomes the fleet

**[Cue]** Click **Join** (top right). The big QR code fills the screen.

> "Scan this. Type your first name. Your phone is now a server in a Basel building."

Wait for the counter under the QR code to go up. Help anyone who's stuck. Give it 20 seconds at most.

**[Cue]** Click anywhere to close the QR code. New pins appear on the map and new rows under **Servers**.

> "Each of you got a building: one's a house, one's a pharma lab. Each building has enough servers for
> all of its heat. DigitalHeat told us there's no heat pump and no backup heater."

### 0:55 · The customer orders

Hand the customer laptop to a jury member.

> "And you're the customer. You want a 3D image rendered. You see the price up front, and you never
> pick a server. Press Order."

If nobody presses it, the Speaker does.

> "The image is cut into sixty parts. The scheduler only hands parts to buildings that need heat right now.
> At minus two, that's everyone."

**[Cue]** Click the **Make it bigger** icon on the job panel at the bottom. Hover a jury member's row under **Servers**:
their parts light up in the image.

> "Look at your phones: orange means rendering. Every part in your colour came from your phone,
> and in real life that heat warms your building, not a data centre's cooling tower."

### 1:40 · One building, close up

**[Cue]** Click the **House** pin, then **3D view** on its card.

> "Here's the reference house from the case. Read it: it needs nine kilowatts of heat right now.
> The little tank shows how much hot water is stored."

Read the servers number from the House row: it should say "eleven of eleven".

> "All eleven of its servers are on. The cold night has emptied its tank, so the house takes every bit
> of their heat, and not a kilowatt-hour more."

**[Cue]** Click **Back to map**.

### 2:05 · The tank is full (the interrupted job)

> "Now the case's hard question: what happens when a building has had enough heat?"

**[Cue]** Click the pin of a jury member's building. Wait until the card says **Working on part … now**,
then click **Fill tank**.

> "Say your family has stopped using hot water and your tank is at a hundred percent. Your rack stops,
> even halfway through a part."

**[Cue]** Point at that part in the image: it shows *saving*, then a percentage. Then point at the dashed
arrow on the map.

> "Your phone saved exactly where it got to. That part is now finishing in another building that still
> needs heat, from the same percentage. Nothing is computed twice. Look at your phone: it says
> your work moved to another server."

> "When your tank cools to ninety percent, your rack switches itself back on."

### 2:45 · July: the work follows the heat

**[Cue]** Click **July**. Snow becomes sun. On the customer laptop, choose **AI reranking**, pick the aspirin
question, and press **Order**.

> "Same fleet, the fifteenth of July, two in the afternoon, twenty-five degrees. A new customer wants an AI
> to rank science abstracts for a claim about aspirin."

Read the House row.

> "The house only needs hot water now: half a kilowatt. One of its eleven servers is on. But the spa still
> heats its pool, and the pharma lab still needs heat all year. That's where this job runs."

> "The scheduler follows the heat, not the queue."

### 3:20 · It's not only on screen

**[Cue]** Switch to the terminal (it's been running since 0:00).

> "This is the same scheduler code controlling a real AI job on this laptop. The laptop is one server
> of the reference house, on that same July day."

Point at the lines as they come:

```
start: 1 of 11 servers have heat
pause (SIGSTOP): no heat this hour, heat again within 2 h
resume (SIGCONT): 1 of 11 servers have heat
```

> "No heat needed: the process pauses. Heat needed again: it carries on from where it was.
> If the heat stays away more than two hours, it saves a checkpoint and can restart on any server."

### 3:45 · What's real, and the close

**[Cue]** Back on `/`, click **Sources** once, then close it.

> "Every number on this screen comes from our Python scheduler, and every assumption has its source
> behind that button. What's simulated: the buildings' heat demand and the tanks, which run sixty times faster
> so you can watch them. What's real: the scheduler, the jobs, and the pause and move."

> "Computing where the heat is wanted. Thank you. Keep your phones: they're still working."

## Making it shorter

| Slot | Cut |
|---|---|
| **3 min** | Skip "One building, close up" (1:40) and the terminal (3:20). Say one sentence instead: "the same pause also runs a real AI job on this laptop; we can show you after." |
| **2 min** | Also skip the jury joining: use the two backup phones. Keep the order, the full tank and July. **Never cut the full tank:** it's the interrupted job the case asks for. |

## What the jury scores, and where it shows

| Criterion | The moment |
|---|---|
| **Transparency (25 %)** | **Sources** at 3:45. "One command reruns the whole year." |
| **Feasibility (25 %)** | Saying what's simulated before anyone asks (3:45). The real process in the terminal (3:20). |
| **Scheduling quality (20 %)** | Parts only go to buildings that need heat (0:55), and the house in July runs one server (2:45). Say "zero heat dumped" out loud. |
| **Creativity (20 %)** | The jury's own phones are the fleet, and a paused part finishes in another building from its last percentage (2:05). |
| **Design (10 %)** | "A homeowner sees one thing: is my building getting heat?" Point at the coloured ring around a tank. |

## If something goes wrong

| Problem | Do this |
|---|---|
| Phones can't open the QR link | "The venue Wi-Fi keeps devices apart." Close the QR code and go on with the two backup phones. |
| The jury won't scan | Same: use the backup phones. Hold one up when you say "look at your phones". |
| Fill tank card says **Between parts** | Wait two seconds and look again, or fill the **Hospital**: it nearly always holds a part. |
| A phone shows **Server offline** | "Someone locked their phone, and their part went straight back to the queue." It's a feature. |
| The render is slow | Don't wait for it. Move on to the full tank at 2:05 anyway. |
| Terminal shows nothing yet | "It's still catching up to July." Skip it and offer to show it after. |
| The website won't load | Play the demo video and keep reading the script over it. |

## Q&A: short answers about the demo

**Is my phone really computing?**
Yes. It path-traces its parts of the image in your browser (or runs the AI model for the reranking job)
and sends them back. In a real building that's a 1 kW server, not a phone.

**Why does the house have 11 servers, when its coldest hour needs 14?**
The tank stores heat from the milder hours for the coldest ones, so 11 is the fewest that cover all of its heat
for the year. DigitalHeat said there's no heat pump and no backup, so every building gets that rack. The yearly
figures on the slides use the same 11.

**Why don't the numbers on screen match the scheduler exactly?**
The tanks are live. Each starts a little below the scheduler's level, as if someone just took a shower, and
the building switches on enough servers for its demand plus refilling the tank within an hour.

**What if every tank in the fleet is full?**
The work waits in the queue. Deadline jobs go first to the building with the most room in its tank.

**Why does the spa keep working in July?**
It heats a pool and a 30 °C hall all year. That's why the fleet mixes homes with sites that need heat in summer.

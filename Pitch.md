# Demo Video Pitch Script (2-3 minutes)

Target length: ~2:30. Timings are approximate speaking pace (~140 wpm).
Speak plainly, don't rush the "no impact" beat, it's the differentiator.

---

## 0:00-0:20 - The problem (hook)

> "If you run a warehouse or a distribution business, you've had this
> moment: an email comes in saying a supplier's factory had a fire, or a
> shipment's stuck at port. And the first question is always the same:
> does this actually affect any of my customers? Today, answering that
> means manually digging through purchase orders, shipment trackers, and
> inventory sheets. This is the Disruption Response Assistant. It answers
> that question in seconds, and it shows its work."

## 0:20-0:45 - What it does, at a glance

> "You paste in the notice exactly as it arrived. No reformatting, no
> structured input. The system reads it, matches whoever's named in it to
> real suppliers, products, or carriers in your data, and then traces the
> actual chain: which purchase orders, which shipments, which customer
> orders are genuinely at risk. Then it ranks them by urgency and gives
> you a short menu of options for each one, expedite, part-ship,
> reallocate, or just notify the customer, with the trade-off spelled
> out."

*(Screen: show the landing page hero, then click into Enter Workspace ->
Operator Access gate -> the workspace.)*

## 0:45-1:30 - Live walkthrough (the core demo)

> "Let's use a real example. A supplier notice: a fire at Coastal Gasket
> Works' Chennai facility, 21-day delay."

*(Paste/select the "Supplier fire" sample, click Analyze.)*

> "In a few seconds: three customer orders are actually exposed, ranked
> by urgency. Order CO1 is a VIP customer, 20 days late, and it's the most
> urgent thing on the board. For each order, you get concrete options,
> here, expediting recovers 12 of the 20 days at roughly double freight
> cost, or we can part-ship 30 units now from stock we already have.
> Every one of these numbers traces back to a specific purchase order and
> shipment ID, you can open that trace and verify it yourself."

*(Point at the source IDs, the recommended badge, the urgency pill.)*

## 1:30-1:55 - The "no impact" case (this is the key differentiator)

> "Here's the part most tools get wrong: not every scary-sounding notice
> actually matters. Watch what happens with an unrelated company."

*(Load the "No impact - unrelated company" sample, click Analyze.)*

> "Nothing in our system depends on this. The assistant says exactly
> that: no impact, no action needed. It doesn't manufacture a story to
> seem useful. That honesty is only possible because the impact tracing
> is deterministic, not the language model guessing."

## 1:55-2:20 - Why it's reliable (the engineering story)

> "Under the hood, the AI only does two things: reading the messy notice
> into structured facts, and writing the final summary paragraph. Every
> number in between, the tracing, the delay math, the urgency ranking,
> is plain Python running against a real relational dataset. And the
> summary itself is checked afterward: if it ever references an ID that
> wasn't part of the verified facts, it's thrown out and replaced with a
> plain, computer-generated one. That's what makes this safe to run on a
> small, fast model instead of something slower and more expensive."

## 2:20-2:30 - Close

> "This is the Disruption Response Assistant, built for the Supply Chain
> track. It turns a messy disruption notice into a traceable, ranked
> action plan, in seconds, and it knows when to say nothing's wrong.
> Thanks for watching."

---

## Shot list (what to actually have on screen)

1. Landing page hero (2-3 sec, let the headline read).
2. Click "Enter Workspace" -> gate page (1-2 sec, don't linger).
3. Type/select operator fields, click "Enter Workspace" -> workspace.
4. Load "Supplier fire - Coastal Gasket Works" sample, click Analyze.
5. Scroll through the summary stats bar, then the CO1 card, hover the
   recommended option.
6. Click Clear, load "No impact - unrelated company", click Analyze.
7. (Optional, if time allows) Quickly show the architecture diagram in
   the README or a terminal running `pytest` to signal it's tested.

## Notes

- Keep narration under the visual, don't read the UI text verbatim, the
  viewer can already see it.
- Cut the "why it's reliable" section short if you're over 2:30, it's the
  most skippable part for a judge who already saw the demo work.
- Record the workspace flow AFTER the AI response has been seen once in
  rehearsal so you know your talking points land inside the actual
  response latency (usually 5-10 seconds).

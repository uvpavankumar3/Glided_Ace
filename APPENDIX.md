# Appendix — Claims & Evidence

Fictional casino, synthetic data (release 0.9.0-draft). Full window Jan 1–Jun 30, 2025. Every figure is reproducible with `./run.sh <path-to-dashboard-royale>`. The same table is on the dashboard's *Claims & evidence* page.

## C1. The manager's bottom 10 are not weak machines: 9 of 10 sit in Back Forty, 2 were already retired in-window, and 1 is a payout anomaly.

- **Table / query:** prepared_daily_view (active) ⋈ machine_day ⋈ game_math → per machine: SUM(house_win), SUM(theo), luck z = (win−theo)/√Σ(bet²·var), peer index vs same theme+zone (leave-one-out)
- **Result:** 0 of 8 remaining machines below 0.90 of same-game peers; bottom-10 luck = −$63,356 on $295,749 theo
- **Alternative explanation tested:** Bad luck: tested with volatility-based z; only M-1158 (z −4.6) is beyond chance. Location: tested with location index (zone/theme vs floor/theme ≈ 0.65 for Back Forty).
- **Limitation:** Peer groups are small (2–12 machines); position within a bank isn't modelled.
- **Dashboard page:** `#machines`

## C2. Back Forty earns ~34% less per available hour on identical games; the walkway closure cut it 30% with no recapture elsewhere.

- **Table / query:** theo / available_hours by zone, 4 weeks before / during (Mar 3–Apr 7) / 4 weeks after the W-ENT-B40 closure, excl. new bank B-51
- **Result:** B40 $14,699 → $10,328 → $13,726/day; rest of floor $119,319 → $119,710
- **Alternative explanation tested:** Seasonality: other zones flat during closure, B40 recovered within a week of reopening.
- **Limitation:** Periods contain different events (Super Bowl vs basketball/conventions).
- **Dashboard page:** `#demand`

## C3. M-1158 pays out more often than its configuration: hit rate 38.6% vs 31.5%.

- **Table / query:** SUM(payout_positive_spins)/SUM(paid_spins) vs game_math.hit_probability; binomial z
- **Result:** z = 124; house win $36,163 below theo
- **Alternative explanation tested:** Luck: a binomial z of 124 is not chance; next-largest |z| on the floor is < 3.
- **Limitation:** A lead to inspect, not proof of a fault or wrongdoing.
- **Dashboard page:** `#machines`

## C4. Adding machines redistributes play: bank B-51 (Mar 24) took ~$5.4k/day of theo but floor theo did not rise.

- **Table / query:** Zone theo/day, Feb 24–Mar 23 vs Apr 7–May 4
- **Result:** Floor $132.2k → $131.2k/day; B-51 $5.4k/day; Center Pit ex-B51 $36.8k → $34.5k
- **Alternative explanation tested:** Seasonal decline masking a gain: possible; April LVCVA visitors were down 5% YoY.
- **Limitation:** One install event; confounded with B40 reopening.
- **Dashboard page:** `#demand`

## C5. Downtime cost ~$90,682 of theo (≈0.39% of theo); Ridgeline (30% of machines) caused 56% of faults.

- **Table / query:** Σ(scheduled − available hours) × machine-month theo per available hour; operations fault_repair by manufacturer
- **Result:** 5,021 machine-hours down; Ridgeline 680 of 1207 faults
- **Alternative explanation tested:** Ridgeline machines played more (more spins → more faults)? Ridgeline theo/hour is not above floor average.
- **Limitation:** Lost theo assumes the machine would have played at its own monthly rate.
- **Dashboard page:** `#downtime`

## C6. Fault waits doubled when day/swing technician slots went unfilled (Apr 14–May 25).

- **Table / query:** shift_roster slot_tech actual < planned; operations wait = work_started − opened
- **Result:** avg wait 0.89 h outside vs 1.91 h inside the gap window
- **Alternative explanation tested:** More faults in the window? Fault counts were lower in Apr–May.
- **Limitation:** Grave-shift (1 tech) waits are long all year; not caused by the gap.
- **Dashboard page:** `#downtime`

## C7. Tracked player results are concentrated: top 10% of players account for ~56% of net losses; 16% finished ahead.

- **Table / query:** player_period summed per player (coin-in > 0); sorted net losses
- **Result:** Top 1% 17.8%, top 10% 56.1%; ahead 16.1%
- **Alternative explanation tested:** Concentration is just play volume? Theo concentration is similar (top 10% = 64% of theo), so losses track exposure, not unusual luck.
- **Limitation:** Carded play only (~66% of coin-in); uncarded guests invisible.
- **Dashboard page:** `#players`

## C8. The May 1 comp-rate cut halved the points price of comps but moved redemptions only +3% and comp cost +4% (vs Mar–Apr), with flat tracked theo and visits. It roughly doubled the comp value of unredeemed points.

- **Table / query:** loyalty_ledger redeem: points ÷ face value per day; redemptions & economic cost per day; player_period Σpoints earned − redeemed
- **Result:** 13.1 → 5.8 pts per comp $; 156M points outstanding ≈ $12M → $27M menu value
- **Alternative explanation tested:** Demand would have fallen without it (June LVCVA visitors −11% YoY)? Can't rule out → randomised pilot.
- **Limitation:** Only 2 post-change months; not randomised; points balance resets each year.
- **Dashboard page:** `#comps`

## C9. A weekday model forecasts daily coin-in with 4.0% error (MAE $53,560) vs 16.4% for a constant mean.

- **Table / query:** Train Jan–Apr (freeze Apr 30), test May–Jun; events used only if announced by the freeze date
- **Result:** Weekday+events MAE $46,125
- **Alternative explanation tested:** Trend model? Test bias is small (+$10k/day weekday model) so trend adds little.
- **Limitation:** Locals Week was announced after the freeze and is excluded; only 2 test months.
- **Dashboard page:** `#model`

## C10. Our observed hold (9.50%) is in line with real Missouri slot hold (~9.6%).

- **Table / query:** property_day Σhouse win/Σcoin-in vs benchmark_state_monthly Σagr/Σhandle
- **Result:** Monthly hold 9.36–9.83% vs Missouri 9.48–9.71%
- **Alternative explanation tested:** Different market mix; benchmark is context only, not a target.
- **Limitation:** Missouri is a different, regional market.
- **Dashboard page:** `#demand`

## C11. Weather does not explain demand: daily coin-in residuals don't track temperature.

- **Table / query:** weekday-model residual (actual ÷ weekday mean − 1) vs NOAA daily max temperature and rain (Las Vegas airport, real data)
- **Result:** corr(residual, tmax) = -0.06; 5 rain days averaged -8.1% vs +1.2% on dry days
- **Alternative explanation tested:** This is itself the alternative tested for the Feb–Jun softening.
- **Limitation:** Only 5 rain days; calendar dates vs gaming dates differ for 6 hours.
- **Dashboard page:** `#demand`

## C12. The bottom 10 is the same when ranked by contribution after supplied costs (leases, service, power, repairs).

- **Table / query:** prepared_daily_view: SUM(contribution_after_supplied_costs_usd) per machine, active days
- **Result:** 9 of 10 machines overlap; 0 machines have negative contribution
- **Alternative explanation tested:** Leased machines' fees could change the ranking; they don't, materially.
- **Limitation:** Supplied costs are partial (no rent, tax, depreciation, full staffing).
- **Dashboard page:** `#machines`

## Priced actions (30 days from July 1, 2025)

Cost = qty × (unit cost + daily cost × max(0, 30 − lead days)).

| Action | Target | Cost | Why (cause) | Expected effect | Uncertainty | Measurement |
|---|---|---|---|---|---|---|
| Inspect & verify paytable of M-1158 (A-INSPECT) | M-1158 (Back Forty, B-31, Desert Gold) | $1,200 | Its hit rate is 38.6% against a configured 31.5% (z = 124) over 674,454 spins, and house win is $36,163 below theo (luck z = -4.6). No other machine has |hit z| above 3. That pattern points to the machine paying differently from its published math (a configuration lead), not bad luck. | If the configuration is corrected, house win returns to theo: about $200/day, or $5,794 over the 29 days after the 1-day lead. | The inspection produces information, not a guaranteed finding. It is a lead to inspect, not proof of wrongdoing or of a fault. | Re-measure hit rate over the next ~112,409 spins (one month). The standard error is about 0.14 pp, so a return to 31.5% ±0.3 pp settles it. Also track luck z for the month. |
| Wayfinding & signage refresh: Back Forty (A-WAYFINDING) | Zone Back Forty (Z-B40) | $7,500 | The same games earn 34% less per available hour in Back Forty than on the floor average. When the Main Entrance to Back Forty walkway closed (Mar 3–Apr 7), Back Forty theo fell 30% while the rest of the floor changed +0.3%. The lost play was not recaptured elsewhere, so access and visibility drive this zone. | Break-even is a 2.8% lift on $13,338/day of Back Forty theo over 20 effective days. Scenarios: 0% → $0; 3% → $8,003; 8% → $21,341. | There's no direct signage history, and the closure shows access matters, not that signs fix it. The comparison periods differ in their events. | Difference-in-differences: Back Forty theo per available hour vs. other zones, 20 days after vs. 28 days before. The frozen July forecast ($39.9M floor coin-in, ±$100k/day 90% error band) checks that any Back Forty lift isn't just a floor-wide swing. Also coverage-adjusted Back Forty entry counts. Freeze the metric before launch. |
| Comp-rate pilot with control group (A-COMP-PILOT) | Tracked players, randomised 50/50 | $4,000 | On May 1 the points price of a comp fell from 13.1 to 5.8 points per comp dollar. Compared with Mar–Apr, redemptions per day rose only +3% and comp cost per day +4%, within the drift that was already there. Tracked theo per month stayed flat ($2,580,670 vs $2,581,170). Meanwhile the 156M unredeemed points are now worth about $27M in comps at menu price, up from $12M at the old rate. The change has no measured return and doubles the comp liability. | Information first. If the control arm (old rate) shows equal theo and visits, revert floor-wide ($1,500) next month. That halves the comp value of the outstanding points again. Comp costs during the pilot still flow through POS cogs. | Two post-change months, seasonality, and a 30-day pilot may be too short to detect small visit effects. Pre-register a minimum detectable effect. | Per-member theo, visits, comp cost and redemption rate, treatment vs. control, with a pre-registered primary metric (theo per member). Randomisation removes seasonality; the July forecast flags any floor-wide shock during the pilot. The pilot cannot be combined with a floor-wide comp change. |

**Total spent $12,700; kept $87,300.**

### Sensitivity (theo-equivalent value: 30 days / 90 days if the effect persists)

| Action | Cost | Low | Base | High |
|---|---|---|---|---|
| Inspect M-1158 | $1,200 | Nothing found: $0 / $0 | 50% chance it's a configuration fault, fixed on day 2: $2,897 / $8,891 | Fault confirmed and fixed on day 2: $5,794 / $17,783 |
| Back Forty wayfinding | $7,500 | No lift: $0 / $0 | 3% lift on Back Forty theo: $8,003 / $32,011 | 8% lift (a quarter of the closure drop): $21,341 / $85,362 |
| Comp-rate pilot | $4,000 | Old rate loses play: keep new rate: $0 / $0 | No difference: revert in August: $0 / $0 | No difference: revert; cost/day back to Mar–Apr level: $0 / $2,708 |
| **Total** | **$12,700** | **$0 / $0** | **$10,900 / $40,902** | **$27,135 / $105,853** |

### Considered and not funded

- **Replace the manager's bottom 10** (A-REPLACE-LEASE / A-REPLACE-BUY, $33,800 leased (16 operating days) or $220,000 purchased (over budget)): None of the 8 bottom-10 machines still on the floor is weak against same-game peers. Two were already retired and replaced (M-1118, M-1120). The slot where M-1120 sat was refilled with the same title (M-5076) and still ranks last, so the slot is the problem, not the cabinet. Adding bank B-51 (+$5,434/day of theo in that bank) did not raise floor theo, so new machines mostly take play from neighbours.
- **Add a technician to a shift** (A-TECH-SHIFT, $11,520): All fault waiting time over six months cost about $4,083 of theo per 30 days at the floor rate. Even eliminating waits entirely would not repay one technician. The April-May wait spike came from unfilled roster slots, not a structural shortage: fill planned shifts instead.
- **Preventive maintenance, Ridgeline (runner-up)** (A-PREVENTIVE, $9,000): Ridgeline has 94 machines (30%) but 680 of 1207 faults. Faults plus lost theo cost about $27,937/month. After the 7-day lead and about $2,521 of sweep downtime, it needs roughly a 54% fault reduction inside 23 days to break even. No data shows what a sweep achieves, so it's runner-up. Fund it if the vendor can show a fault-reduction record.
- **Promotion weekend (runner-up)** (A-PROMO, $15,000): The February slot tournament ran about 17% above the weekday model. The week-long Locals event was followed by below-model weeks. One success and one mixed result is too thin to bet $15k on, and promotions must avoid targeting heavy losers.

## Model validation

- Freeze date 2025-04-30: trained on Jan–Apr, tested on May–Jun (61 unseen days). Inputs: weekday, and events announced by the freeze date.
- MAE: constant mean $218,258/day; weekday mean $53,560; weekday + known events $46,125 (chosen).
- July baseline (refit on Jan–Jun, frozen before July): $39,948,843 floor coin-in, 90% daily error band ±$99,636. Used as the counterfactual when measuring the actions.

## AI-use disclosure

- **Claude (Anthropic)** was used to explore the data, write the analysis pipeline (DuckDB/pandas), build the single-file HTML dashboard, and draft this appendix, the write-up.
- All numbers come from the pipeline in `pipeline/` run on the official challenge data. I reviewed the method choices (luck z-score, peer and location indices, time-based model holdout, action pricing) and the conclusions.


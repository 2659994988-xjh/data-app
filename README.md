# XuJinghan · Delivery Lens · Olist Delivery Performance Monitor

**BANA409 in-class data app exercise.** This repository contains a Streamlit dashboard and its documented business decisions. The [class exercise](https://bana409.harrywang.me/docs/lectures/data-app/in-class-group-exercise) emphasizes the choice of decision-maker, metrics, page order, refresh cadence, and limitations over the number of features.

> **One decision:** If the Olist logistics operations manager sees that the weekly late-delivery rate rises and a destination state accounts for many late orders, they will investigate that state's fulfilment and carrier records and coordinate corrective action. The state breakdown is a *triage signal*, not proof that the destination caused the delay.

## 1. Dataset and decision-maker

- **Source:** [Brazilian E-Commerce Public Dataset by Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), published by Olist. Olist describes it as anonymized **real commercial data** from about 100,000 orders placed in 2016–2018 across Brazilian marketplaces. License shown on Kaggle: CC BY-NC-SA 4.0.
- **One row:** one order. The app uses order status, purchase date, carrier hand-off date, actual delivery date, promised delivery date, destination state, and product categories. A single order can have multiple items and categories; its categories are combined into one field.
- **Committed file:** [`data/olist_delivery_orders.csv`](data/olist_delivery_orders.csv), 99,441 rows and about 13.90 MB. It joins the original orders to customers on `customer_id` and aggregates item/product categories by `order_id`. Joins are validated so each order remains one row. No orders were sampled or fabricated. The original ZIP is excluded from the repository. Reproduce the file with `python scripts/prepare_data.py path/to/olist.zip`.
- **Analysis window:** promised delivery dates **2017-03-01 to 2018-08-31**. The raw file extends from September 2016 to November 2018, but the early and late promise months have very few or incomplete observations. The default dashboard excludes those edge months; the source CSV preserves them for audit.
- **Decision-maker:** one role, the **Olist logistics operations manager**, who reviews service reliability by destination and coordinates investigation with fulfilment and carrier teams.

## 2. Why this is a dashboard

1. **Who looks at it, and how often?** The intended viewer is the **Olist logistics operations manager**. In a production workflow, they would review it **every Monday** to assess the last completed weeks. Order and carrier data would refresh nightly; the public Kaggle snapshot in this prototype does not refresh.

2. **What decision does it support?** *If the logistics operations manager sees that a completed week's late-delivery rate is at least 3 percentage points above the previous four completed weeks' combined rate, with at least 100 eligible orders, they will inspect the affected destination states and underlying handoff records, then coordinate an investigation with fulfilment and carrier teams.* This is a proposed investigation rule, not an Olist contractual target. The red **>15%** card status is a simpler visual prompt for the selected period; it is not proof of a cause or an automatic alert.

3. **What do they do without it, and what does that cost?** They would export order and carrier records, match promised and actual delivery dates, calculate late rates by week, and compare destination states manually. Repeating those steps takes analyst time and can delay noticing a deterioration or prioritizing the wrong region. The public dataset contains no staff-time records, complaint costs, or service-level penalties, so a monetary or hourly saving cannot be estimated credibly.

4. **Why a dashboard rather than a weekly email, report, or alert?** The manager needs to repeat the check and change the date or state filter when a rate worsens. A weekly email can announce one summary number, but cannot readily show the trend, regional breakdown, and underlying orders for follow-up. A static report becomes outdated as new orders arrive. A single-threshold alert is useful for an urgent breach, but lacks the context needed to choose where to investigate. The dashboard keeps those views together for the weekly review; a production alert could complement it for urgent exceptions.

## 3. What is shown, and what is cut

### Metric definitions

An **eligible order** has `order_status == "delivered"` and valid actual and promised delivery dates. Both timestamps are reduced to **calendar dates**; delivery later on the promised day is still on time. A **late order** has `actual delivery date > promised delivery date`.

1. **Late-delivery rate** = late eligible orders / all eligible orders within the filters. The denominator is visible in chart hover text and is not all orders placed.
2. **Late orders** = count of eligible orders whose actual date is after the promise date.
3. **Median days late** = median of positive calendar-day differences for late orders only. This resists a few extreme delays.

The late-rate card shows a **proposed review status for the selected date and state filters**: below 5% = lower, 5% through 15% = attention, above 15% = high risk (red). These are illustrative operating bands requested for the prototype, **not** an Olist service-level target or a live alert. The percentage and status are calculated from the same filtered eligible-order denominator.

**Supporting charts:** (1) weekly late rate answers *when* performance changed; (2) destination states ranked by **late-order count** answers *where the most affected orders are*. The second chart includes rate and sample count in hover text, and excludes states with fewer than 200 eligible orders in the selected period. The top 20 late orders appear below for historical investigation. Their table shows product categories, hand-off date, hand-off-to-delivery days, and whether hand-off had already missed the promise date. Only promised-date and single destination-state filters are included, because these change the manager's review.

**Page order:** title and decision → three headline metrics → two diagnostic charts → order detail → definition and limitation. It follows the manager's path from “is there a problem?” to “where should I look?”

**Deliberately excluded:**

- Payment method and basket value: interesting commercial fields, but they do not change the logistics manager's first investigation decision and require extra joins.
- Customer review scores: reviews might show an association with delay, but they are a different outcome and can be missing or influenced by other causes. Adding them would distract from delivery reliability.

### Quick EDA and limitations

The notebook [`notebooks/eda.ipynb`](notebooks/eda.ipynb) checks shape, missing values, status distribution, lateness distribution, weekly trends, and state differences with Pandas and Matplotlib. Observed in the full committed file: 99,441 unique orders; 2,965 missing actual-delivery timestamps; 1,783 missing carrier hand-off timestamps; 96,478 orders marked delivered. Eight delivered orders also lack an actual timestamp, so 96,470 delivered orders have enough dates for the lateness calculation across the full snapshot. In the chosen complete-month window there are **93,901 eligible orders and 6,520 late orders (6.94%)**.

Risks of misinterpretation:

- **Retrospective, delivered-only measure.** Undelivered, cancelled, or unavailable orders are not counted as on time or late. This is not a current overdue-order queue and may understate customer-facing delivery failures. A production version should monitor open overdue orders separately.
- **Historical snapshot.** Kaggle marks the dataset's expected update frequency as **never**. The page must not be presented as live 2026 Olist performance.
- **Incomplete edge months.** Sparse 2016 and late-2018 promise months are outside the default window. An incomplete recent cohort should likewise be withheld in production until outcomes mature.
- **No causal claim from geography.** Destination state locates an investigation; the data does not isolate carrier, distance, warehouse, weather, or seller effects. Extremely small state samples are withheld from the ranking.
- **No warehouse/carrier attribution.** The source has no warehouse ID or carrier company ID. Hand-off after the promised day proves the promise was already missed before carrier hand-off, but does not prove a warehouse fault. Hand-off on or before the promise day followed by late delivery suggests investigating the downstream journey, but does not prove carrier fault. A product category is an association, not a cause. Orders can contain multiple categories.
- **Extreme delays.** A few delivered orders appear more than 100 days late. The median KPI reduces their influence, while the detail table keeps them visible for source-record verification; they are not silently discarded.

## 4. Refresh and action rule

**Prototype:** fixed Kaggle snapshot, no automatic data refresh. The app explicitly displays its 2017–2018 analysis period.

**Real Olist workflow:** ingest order and carrier status updates **nightly** after the daily fulfilment close; refresh the metrics the next morning. The manager reviews the dashboard **every Monday**. Weekly rate should be computed from promise-date cohorts after enough time for delivery status to settle. This cadence is fast enough for a weekly coordination meeting and avoids the cost and noise of recalculating an aggregate dashboard every minute. A separate operational alert would handle an individual order already past promise while still undelivered.

**Proposed investigation trigger, not an Olist SLA:** investigate if a completed week's late rate is at least **3 percentage points above the previous four completed weeks' combined rate**, provided the week has at least **100 eligible orders**. Check the affected destination states and underlying carrier hand-off records before assigning a cause. This is a starting rule to validate against future data, not a threshold inferred from a contractual target.

If the feed is stale by a day, the weekly review might miss recently delivered exceptions. A week of stale data could delay identifying a broad regional deterioration until the following meeting. The dashboard should display its latest ingested date in a live deployment.

## 5. Run locally and deploy

This repository was initialized with `uv init`. Run from the repository root:

```bash
uv sync
uv run streamlit run app.py
```

Or install `requirements.txt` in a Python environment and run `streamlit run app.py`.

For **Streamlit Community Cloud**, select this public GitHub repository and `app.py` as the entry point, set Python to **3.14** under Advanced settings as required by the course, then deploy. The data file is committed, so no Kaggle credential is needed at app runtime. Submit the deployed app URL and the repository URL individually on Canvas. The user will perform this deployment step.

## Source and transformation

Original data: Olist, [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). The compact CSV is an attributed educational derivative retaining the source's anonymized order data. Preparation code and the exact exclusions are in this repository. The repository's MIT `LICENSE` applies to the original app code; the Olist-derived CSV remains under the dataset's CC BY-NC-SA 4.0 terms.


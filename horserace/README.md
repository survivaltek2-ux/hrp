Horse Race Prediction Pipeline

Overview
- Trains a per-horse win model and converts scores into per-race probabilities that sum to 1 using a softmax across runners in the same race.
- Focuses on pragmatic features available in typical historical datasets.

Key ideas
- Supervised model on per-horse rows with target `won` (1 if finish_position == 1 else 0).
- During inference, compute each runner’s raw score (log-odds) and apply a race-softmax to produce well-calibrated probabilities that sum to 1 in each race.
- Simple, extendable feature pipeline with numeric features and high-cardinality categorical handling via frequency-capped one-hot.

Dependencies
- Python 3.9+
- pandas, numpy, scikit-learn, joblib, requests (for API ingest)

Data schema (CSV)
- Required columns:
  - `race_id` (str/int): unique race identifier
  - `horse_id` (str/int): horse identifier
  - `finish_position` (int): finishing rank (1 = winner)
  - `distance_meters` (float)
  - `draw` (int): post position / stall
  - `weight_carried` (float): e.g., kilograms or pounds
  - `going` (str): track condition (e.g., Firm/Good/Soft)
  - `race_class` (str/int): class/grade/band
  - `age` (int)
  - `days_since_last_run` (int)
  - `jockey` (str)
  - `trainer` (str)
- Optional columns (used if present):
  - `official_rating` (float), `speed_figure` (float), `field_size` (int), `date` (YYYY-MM-DD), `odds` (float)

Quickstart
1) Train
   - `python -m horserace.train --train_csv horserace/example_train.csv --out_model artifacts/model.joblib`

2) Predict on a race card
   - `python -m horserace.predict --model artifacts/model.joblib --card_csv horserace/example_card.csv --out_csv artifacts/predictions.csv`

Integrate TheRacingAPI
- Auth options (prefer Basic Auth):
  - Basic Auth (recommended):
    - `export THERACINGAPI_USERNAME=your_user`
    - `export THERACINGAPI_PASSWORD=your_pass`
  - API key (fallback):
    - `export THERACINGAPI_KEY=...`
    - `export THERACINGAPI_KEY_HEADER=x-api-key` (override if different)
- Base URL:
  - `export THERACINGAPI_BASE=https://api.theracingapi.com` (override if different)
- Fetch results into CSV for training:
  - `python -m horserace.ingest_theracingapi results --start_date 2024-01-01 --end_date 2024-01-07 --out_csv data/results_2024w1.csv`
- Fetch a race card for a date:
  - `python -m horserace.ingest_theracingapi racecard --date 2024-01-08 --out_csv data/card_2024-01-08.csv`
- Train and predict using the produced CSVs as usual.

Notes on mapping
- The ingest attempts to map common JSON keys to the pipeline schema and supports unit conversion for distance (`m|f|y|km`) and weight (`kg|lb`).
- If your provider uses different JSON shapes, tweak `horserace/data_sources/theracingapi.py` endpoints and field extraction.

Notes
- If you include `odds`, it can dominate signal; consider training with and without it.
- Add more domain features (e.g., surface, pace, sectional times) to improve accuracy.
- For multiple jurisdictions, encode jurisdiction/track to avoid distribution shift.

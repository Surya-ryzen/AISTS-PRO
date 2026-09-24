# Week 11: forecasting AI and backend

The integrated backend runs locally on port 8000 with PostgreSQL. Start from the project root with `python -m backend.scripts.run_local`. This local launcher adds missing tables without dropping existing data. It runs one server process; do not use multiple workers with its in-process training queue and camera loop.

## Implemented

- Source/run/layout-scoped streams, immutable complete-minute samples, model versions, training jobs and prediction history in PostgreSQL.
- Six lagged minutes of visible vehicle count, estimated speed and queue length. Direct forecasts at 1, 5 and 15 minutes use ridge regression or a last-value baseline, selected separately per output on chronological validation data.
- Chronological 60/20/20 training/validation/test partitions with a horizon gap. Standardization is fitted only on training data during evaluation. Saved MAE/RMSE are pre-refit holdout scores; deployable coefficients are then fitted on all supplied history.
- Exact additive feature contributions, intercept and nonnegative clipping adjustment accompany every forecast. Contributions explain the model calculation, not causal effects. No fabricated accuracy percentage or confidence interval.
- Persistent shared prediction cache keyed by stream, lane, horizon, last immutable input minute and model version. New data/models invalidate keys; freshness is checked before returning cached live data.
- Authenticated reads and administrator-only imports/training; lane/horizon/range validation, transactional import, idempotent retries, concurrent PostgreSQL stream locking, stale/gapped/future data rejection.
- Background training job status and errors. Interrupted jobs are marked failed on restart and can be resubmitted. Completed source minutes trigger inference where an appropriate model exists. First training/retraining is explicitly submitted through the API.
- Live samples use completed UTC epoch minutes. Recorded files use source-relative minutes. Loops and layout changes create separate streams. Short clips cannot manufacture training history by replaying.

## API workflow

1. Authenticate at `POST /auth/login` and send its bearer token.
2. `POST /forecasting/streams`: source, run_id, layout_id, data_kind (`live`, `recorded`, `synthetic`). Save the returned id.
3. `POST /forecasting/streams/{id}/samples`: samples with lane_id, minute, vehicle_count, average_speed, queue_length. Inputs are immutable; corrections require a new stream version.
4. `POST /forecasting/streams/{id}/train`: lane_id and horizon (1/5/15). Returns a job id. Training requires at least 92/100/120 consecutive minute measurements, respectively. These minima are software requirements, not evidence of a representative dataset.
5. `GET /forecasting/jobs/{id}` and `/forecasting/models/{id}` expose job state, model version and evaluation.
6. `GET /forecasting/streams/{id}/lanes/{lane}?horizon=5` returns predictions/explanations; `/forecasting/streams/{id}/history` returns saved results.
7. `GET /predictions/lanes/{lane}` is a convenience endpoint for the newest live stream and one-minute horizon. Use explicit stream endpoints when selecting a source matters.

## Verification and limits

Live PostgreSQL verification trained and served all three horizons, checked cache misses/hits and persisted history. Its source is explicitly `backend-integration-check`, data_kind `synthetic`; it is not real traffic accuracy evidence. The reusable verifier is `backend/scripts/verify_forecasting.py` (requires a local password file).

Existing demonstration traffic clips last roughly 13-28 seconds. Legacy analytics mix repeated sessions without source identity. Neither supplies continuous representative data to validate forecasting. A real lane dataset with sufficient uninterrupted minutes and a longer, separately held-out evaluation period is still required. Speeds inherit existing camera calibration error. Counts represent visible vehicles, not arrival volume. Forecasts do not automatically control physical traffic signals.

The earlier exponential-smoothing baseline remains in service.py for comparison/tests; production routes use runtime.py and source-scoped records.

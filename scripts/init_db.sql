-- Extensions (TimescaleDB comes pre-installed in the timescale/timescaledb image)
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ── Daily Prices (hypertable) ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS daily_prices (
    time        TIMESTAMPTZ    NOT NULL,
    ticker      TEXT           NOT NULL,
    open        DOUBLE PRECISION,
    high        DOUBLE PRECISION,
    low         DOUBLE PRECISION,
    close       DOUBLE PRECISION,
    adj_close   DOUBLE PRECISION,
    volume      BIGINT
);

SELECT create_hypertable('daily_prices', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS ix_daily_prices_ticker_time
    ON daily_prices (ticker, time DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_daily_prices_ticker_time
    ON daily_prices (ticker, time);

-- ── Daily Returns (hypertable) ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS daily_returns (
    time         TIMESTAMPTZ    NOT NULL,
    ticker       TEXT           NOT NULL,
    return_1d    DOUBLE PRECISION
);

SELECT create_hypertable('daily_returns', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS ix_daily_returns_ticker_time
    ON daily_returns (ticker, time DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_daily_returns_ticker_time
    ON daily_returns (ticker, time);

-- ── FRED Observations (hypertable) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS fred_observations (
    time       TIMESTAMPTZ    NOT NULL,
    series_id  TEXT           NOT NULL,
    value      DOUBLE PRECISION
);

SELECT create_hypertable('fred_observations', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS ix_fred_obs_series_time
    ON fred_observations (series_id, time DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_fred_obs_series_time
    ON fred_observations (series_id, time);

-- ── Corporate Actions (hypertable) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS corporate_actions (
    time         TIMESTAMPTZ    NOT NULL,
    ticker       TEXT           NOT NULL,
    action_type  TEXT           NOT NULL,   -- dividend / split
    value        DOUBLE PRECISION,
    details      JSONB
);

SELECT create_hypertable('corporate_actions', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS ix_corp_actions_ticker_time
    ON corporate_actions (ticker, time DESC);

CREATE UNIQUE INDEX IF NOT EXISTS uq_corp_actions_ticker_time_type
    ON corporate_actions (ticker, time, action_type);

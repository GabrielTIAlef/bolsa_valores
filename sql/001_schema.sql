CREATE TABLE IF NOT EXISTS dim_ativo (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    currency TEXT NOT NULL CHECK (currency = 'USD')
) STRICT;
CREATE TABLE IF NOT EXISTS dim_data (
    date TEXT PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year_month TEXT NOT NULL,
    month_index INTEGER NOT NULL
) STRICT;
CREATE TABLE IF NOT EXISTS fato_cotacao (
    symbol TEXT NOT NULL REFERENCES dim_ativo(symbol),
    date TEXT NOT NULL REFERENCES dim_data(date),
    open REAL NOT NULL CHECK (open > 0 AND open <= 1000000000),
    high REAL NOT NULL CHECK (high > 0 AND high <= 1000000000),
    low REAL NOT NULL CHECK (low > 0 AND low <= 1000000000),
    close REAL NOT NULL CHECK (close > 0 AND close <= 1000000000),
    adjusted_close REAL NOT NULL CHECK (adjusted_close > 0 AND adjusted_close <= 1000000000),
    volume INTEGER NOT NULL CHECK (volume >= 0 AND volume <= 1000000000000),
    PRIMARY KEY (symbol, date),
    CHECK (low <= open AND low <= close AND high >= open AND high >= close AND low <= high)
) STRICT;
CREATE TABLE IF NOT EXISTS metadata (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL
) STRICT;
CREATE VIEW IF NOT EXISTS vw_mensal AS
WITH ordered AS (
    SELECT q.*, d.year_month, d.month_index,
           ROW_NUMBER() OVER (PARTITION BY q.symbol, d.year_month ORDER BY q.date DESC) AS rn
    FROM fato_cotacao q JOIN dim_data d ON d.date = q.date
)
SELECT symbol, year_month AS month, MAX(month_index) AS month_index,
       COUNT(*) AS observations, AVG(close) AS mean_close, SUM(volume) AS volume,
       MAX(CASE WHEN rn = 1 THEN adjusted_close END) AS last_adjusted_close
FROM ordered GROUP BY symbol, year_month;
CREATE VIEW IF NOT EXISTS vw_mensal_retorno AS
WITH previous AS (
    SELECT *, LAG(month_index) OVER w AS previous_index,
           LAG(last_adjusted_close) OVER w AS previous_close,
           LAG(mean_close) OVER w AS previous_mean
    FROM vw_mensal WINDOW w AS (PARTITION BY symbol ORDER BY month_index)
)
SELECT symbol, month, observations, mean_close, volume, last_adjusted_close,
       CASE WHEN month_index - previous_index = 1 THEN last_adjusted_close / previous_close - 1 END AS return_monthly_price,
       CASE WHEN month_index - previous_index = 1 THEN mean_close / previous_mean - 1 END AS mean_close_mom
FROM previous;

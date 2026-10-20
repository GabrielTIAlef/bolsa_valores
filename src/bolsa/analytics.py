"""Retornos e medidas por ativo; primeiros valores indefinidos continuam ausentes."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from .contracts import Dataset, validate

ANNUALIZATION = 252


@dataclass
class Analysis:
    dataset: Dataset
    daily: pd.DataFrame
    monthly: pd.DataFrame
    summary: pd.DataFrame


def analyze(dataset):
    dataset = validate(dataset)
    daily = dataset.quotes.copy()
    daily['return_daily'] = daily.groupby('symbol').adjusted_close.pct_change(fill_method=None)
    grouped = daily.groupby('symbol', sort=False)
    daily['base_100'] = 100 * daily.adjusted_close / grouped.adjusted_close.transform('first')
    daily['drawdown'] = daily.adjusted_close / grouped.adjusted_close.cummax() - 1
    daily['momentum_21'] = grouped.adjusted_close.pct_change(periods=21, fill_method=None)
    daily['volatility_20_annualized'] = grouped.return_daily.transform(
        lambda s: s.rolling(20, min_periods=20).std(ddof=1) * np.sqrt(ANNUALIZATION))
    daily['month'] = daily.date.str[:7]
    monthly = daily.groupby(['symbol', 'month'], as_index=False).agg(
        first_date=('date', 'first'), last_date=('date', 'last'), observations=('date', 'size'),
        open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'),
        mean_close=('close', 'mean'), last_adjusted_close=('adjusted_close', 'last'), volume=('volume', 'sum'))
    month_index = pd.PeriodIndex(monthly.month, freq='M').asi8
    monthly['month_index'] = month_index
    grouped_months = monthly.groupby('symbol', sort=False)
    consecutive = grouped_months.month_index.diff().eq(1)
    monthly['return_monthly_price'] = grouped_months.last_adjusted_close.pct_change(fill_method=None).where(consecutive)
    monthly['mean_close_mom'] = grouped_months.mean_close.pct_change(fill_method=None).where(consecutive)
    starts = pd.to_datetime(monthly.month + '-01')
    ends = starts + pd.offsets.MonthEnd(0)
    monthly['period_complete_declared'] = ((starts >= pd.Timestamp(dataset.metadata['coverage_start'])) &
                                            (ends <= pd.Timestamp(dataset.metadata['coverage_end'])))
    monthly['return_periods_complete_declared'] = (monthly.period_complete_declared &
        monthly.groupby('symbol').period_complete_declared.shift(1, fill_value=False) & consecutive)
    rows = []
    for symbol, frame in daily.groupby('symbol'):
        returns = frame.return_daily.dropna()
        rows.append({'symbol': symbol, 'observations': len(frame), 'first_date': frame.date.iloc[0],
                     'last_date': frame.date.iloc[-1], 'return_window_price': frame.adjusted_close.iloc[-1] / frame.adjusted_close.iloc[0] - 1,
                     'volatility_annualized': returns.std(ddof=1) * np.sqrt(ANNUALIZATION) if len(returns) >= 2 else np.nan,
                     'max_drawdown': frame.drawdown.min(), 'volume': int(frame.volume.sum())})
    return Analysis(dataset, daily.drop(columns='month'), monthly.drop(columns='month_index'), pd.DataFrame(rows))


def narrative(analysis):
    origin = 'Dados integralmente fictícios.' if analysis.dataset.metadata['synthetic'] else 'Dados fornecidos; origem declarada pelo usuário.'
    lines = [origin, 'Resumo descritivo de retorno de preço ajustado por split; não inclui dividendos.',
             'Volume é quantidade de ações e não mede sozinho a liquidez.']
    for row in analysis.summary.itertuples(index=False):
        lines.append(f'{row.symbol}: {row.observations} observações de {row.first_date} a {row.last_date}; '
                     f'variação de preço no intervalo {row.return_window_price:.2%}; drawdown mínimo {row.max_drawdown:.2%}; '
                     f'volume bruto {row.volume} ações.')
    lines.append('Não há previsão, ranking de investimento ou sinal de compra/venda.')
    return '\n'.join(lines) + '\n'

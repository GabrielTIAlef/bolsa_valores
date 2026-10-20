"""Séries inventadas; dias úteis fictícios não são sessões NASDAQ."""
import numpy as np
import pandas as pd
from .contracts import ASSET_COLUMNS, Dataset, QUOTE_COLUMNS


def generate(seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range('2024-01-01', '2024-12-31')
    assets, frames = [], []
    split_index = len(dates) // 2
    for i in range(6):
        symbol = f'DEMO_{chr(65+i)}'
        assets.append([symbol, f'Ativo ficticio {chr(65+i)}', 'USD'])
        latent = (45 + 15 * i) * np.exp(np.cumsum(rng.normal(.0003 + i * .00005, .009 + .001 * i, len(dates))))
        factor = np.where(np.arange(len(dates)) < split_index, 2., 1.) if i == 0 else np.ones(len(dates))
        close = np.round(latent * factor, 6)
        opened = np.round(close * np.exp(rng.normal(0, .003, len(dates))), 6)
        volume = rng.integers(100000, 900000, len(dates), dtype=np.int64)
        if i == 0:
            volume[split_index:] *= 2
        frames.append(pd.DataFrame({'symbol': symbol, 'date': dates.strftime('%Y-%m-%d'),
            'open': opened, 'high': np.round(np.maximum(opened, close) * 1.005, 6),
            'low': np.round(np.minimum(opened, close) * .995, 6), 'close': close,
            'adjusted_close': np.round(latent, 6), 'volume': volume})[QUOTE_COLUMNS])
    metadata = {'synthetic': True, 'currency': 'USD', 'adjustment_basis': 'split_only',
                'calendar': 'synthetic_weekdays', 'coverage_start': '2024-01-01', 'coverage_end': '2024-12-31',
                'sessions': dates.strftime('%Y-%m-%d').tolist(), 'seed': seed,
                'split_demo': {'symbol': 'DEMO_A', 'date': dates[split_index].strftime('%Y-%m-%d'), 'ratio': 2},
                'origin': 'Gerador local; não são cotações de empresas ou de uma bolsa real.'}
    return Dataset(pd.DataFrame(assets, columns=ASSET_COLUMNS), pd.concat(frames, ignore_index=True), metadata)

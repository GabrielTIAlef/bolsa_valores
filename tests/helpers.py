import numpy as np
import pandas as pd
from bolsa.contracts import ASSET_COLUMNS, Dataset, QUOTE_COLUMNS


def make(prices=(100., 110., 99.), *, dates=None, raw=None, second=False):
    dates = list(dates) if dates is not None else pd.bdate_range('2024-01-01', periods=len(prices)).strftime('%Y-%m-%d').tolist()
    raw = list(prices) if raw is None else list(raw)
    assets = [['TEST_A', 'Test asset A', 'USD']]
    rows = [['TEST_A', d, p, p * 1.01, p * .99, p, adj, 100 + i]
            for i, (d, p, adj) in enumerate(zip(dates, raw, prices))]
    if second:
        assets.append(['TEST_B', 'Test asset B', 'USD'])
        rows.extend([['TEST_B', d, 200., 202., 198., 200., 200., 200] for d in dates])
    meta = {'synthetic': True, 'currency': 'USD', 'adjustment_basis': 'split_only',
            'calendar': 'declared_sessions', 'coverage_start': min(dates), 'coverage_end': max(dates), 'sessions': sorted(dates)}
    return Dataset(pd.DataFrame(assets, columns=ASSET_COLUMNS), pd.DataFrame(rows, columns=QUOTE_COLUMNS), meta)

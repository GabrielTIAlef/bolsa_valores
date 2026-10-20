"""SQLite real, snapshot transacional e reconciliação de resultados SQL/Python."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import numpy as np
import pandas as pd
from .contracts import DataError, validate

ROOT = Path(__file__).resolve().parents[2]


def connect(path):
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA foreign_keys = ON')
    return connection


def initialize(connection):
    if connection.in_transaction:
        raise DataError('Inicialização exige conexão sem transação ativa.')
    connection.executescript((ROOT / 'sql/001_schema.sql').read_text(encoding='utf-8'))


def load_snapshot(connection, dataset):
    dataset = validate(dataset)
    if connection.in_transaction or connection.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
        raise DataError('Carga exige conexão sem transação ativa e foreign keys habilitadas.')
    dates = dataset.metadata['sessions']
    with connection:
        connection.execute('DELETE FROM fato_cotacao')
        connection.execute('DELETE FROM dim_ativo')
        connection.execute('DELETE FROM dim_data')
        connection.executemany('INSERT INTO dim_ativo VALUES (?, ?, ?)', dataset.assets.itertuples(index=False, name=None))
        connection.executemany('INSERT INTO dim_data VALUES (?, ?, ?, ?, ?)',
            [(s, int(s[:4]), int(s[5:7]), s[:7], int(s[:4]) * 12 + int(s[5:7])) for s in dates])
        connection.executemany('INSERT INTO fato_cotacao VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                               dataset.quotes.itertuples(index=False, name=None))
        connection.execute('INSERT INTO metadata VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',
                           (json.dumps(dataset.metadata, ensure_ascii=False, allow_nan=False),))
        count, volume = connection.execute('SELECT COUNT(*), SUM(volume) FROM fato_cotacao').fetchone()
        if count != len(dataset.quotes) or volume != int(dataset.quotes.volume.sum()):
            raise DataError('Reconciliação SQL de linhas/volume falhou.')


def reconcile(connection, analysis):
    sql = pd.read_sql_query('SELECT * FROM vw_mensal_retorno ORDER BY symbol, month', connection)
    py = analysis.monthly.sort_values(['symbol', 'month']).reset_index(drop=True)
    if sql[['symbol', 'month']].to_dict('records') != py[['symbol', 'month']].to_dict('records'):
        raise DataError('Chaves mensais SQL/Python divergentes.')
    for column in ('observations', 'volume', 'mean_close', 'last_adjusted_close', 'return_monthly_price', 'mean_close_mom'):
        if not np.allclose(sql[column].to_numpy(dtype=float), py[column].to_numpy(dtype=float),
                           rtol=1e-10, atol=1e-10, equal_nan=True):
            raise DataError('Resultados mensais SQL/Python divergentes.')
    if connection.execute('PRAGMA foreign_key_check').fetchall() or connection.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise DataError('Integridade SQLite não confirmada.')
    return {'monthly_rows': len(sql), 'quotes': len(analysis.daily), 'status': 'passed'}


def build(path, analysis):
    # O chamador controla a pasta de staging. Não sobrescrever bancos existentes.
    path = Path(path)
    if path.exists():
        raise DataError('O arquivo SQLite de destino já existe.')
    with closing(connect(path)) as connection:
        initialize(connection)
        load_snapshot(connection, analysis.dataset)
        return reconcile(connection, analysis)

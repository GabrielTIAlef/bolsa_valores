"""Uma cotação por ativo/sessão declarada; nenhuma imputação de preços."""
from dataclasses import dataclass
import copy
from datetime import date
import re
import numpy as np
import pandas as pd

PRICES = ['open', 'high', 'low', 'close', 'adjusted_close']
QUOTE_COLUMNS = ['symbol', 'date', *PRICES, 'volume']
ASSET_COLUMNS = ['symbol', 'name', 'currency']


class DataError(ValueError):
    """Mensagem sem valores privados ou caminhos de entrada."""


@dataclass
class Dataset:
    assets: pd.DataFrame
    quotes: pd.DataFrame
    metadata: dict


def iso(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise DataError('Datas devem ser textos ISO YYYY-MM-DD sem horário.')
    try:
        parsed = date.fromisoformat(value)
        if not 1900 <= parsed.year <= 2100:
            raise ValueError
    except ValueError:
        raise DataError('Data de calendário inválida.') from None
    return value


def validate(dataset):
    if not isinstance(dataset, Dataset) or not isinstance(dataset.metadata, dict):
        raise DataError('Dataset e metadados são obrigatórios.')
    if not isinstance(dataset.assets, pd.DataFrame) or not isinstance(dataset.quotes, pd.DataFrame):
        raise DataError('Ativos e cotações devem ser tabelas.')
    assets, quotes = dataset.assets.copy(deep=True), dataset.quotes.copy(deep=True)
    meta = copy.deepcopy(dataset.metadata)
    allowed = {'synthetic', 'currency', 'adjustment_basis', 'calendar', 'coverage_start', 'coverage_end',
               'sessions', 'seed', 'split_demo', 'origin'}
    if set(meta) - allowed:
        raise DataError('Metadados adicionais não são aceitos; não inclua credenciais ou configurações privadas.')
    if 'seed' in meta and (isinstance(meta['seed'], bool) or not isinstance(meta['seed'], int) or not 0 <= meta['seed'] < 2**32):
        raise DataError('Semente inválida.')
    if 'origin' in meta and (not isinstance(meta['origin'], str) or not 1 <= len(meta['origin']) <= 300):
        raise DataError('Descrição de origem inválida.')
    if list(assets.columns) != ASSET_COLUMNS or list(quotes.columns) != QUOTE_COLUMNS:
        raise DataError('Colunas e ordem devem seguir o contrato de ativos e cotações.')
    if not 1 <= len(assets) <= 20 or not 2 <= len(quotes) <= 20000:
        raise DataError('Aceitos 1–20 ativos e 2–20000 cotações.')
    if not assets.symbol.map(lambda s: isinstance(s, str) and bool(re.fullmatch(r'[A-Z][A-Z0-9_]{0,15}', s))).all():
        raise DataError('Símbolos inválidos.')
    if assets.symbol.duplicated().any() or assets.isna().any().any():
        raise DataError('Ativos precisam ser únicos e completos.')
    if not assets.name.map(lambda s: isinstance(s, str) and bool(re.fullmatch(r'[A-Za-z0-9 _-]{1,64}', s)) and s[0].isalnum()).all():
        raise DataError('Nomes de ativos devem seguir o formato seguro documentado.')
    if not assets.currency.eq('USD').all() or meta.get('currency') != 'USD':
        raise DataError('O contrato aceita somente uma moeda: USD, sem conversão cambial.')
    if not isinstance(meta.get('synthetic'), bool) or meta.get('adjustment_basis') != 'split_only':
        raise DataError('Declare a origem e a política split_only; retorno total não é suportado.')
    if meta.get('calendar') not in ('synthetic_weekdays', 'declared_sessions'):
        raise DataError('Calendário não suportado.')
    if meta['calendar'] == 'synthetic_weekdays' and not meta['synthetic']:
        raise DataError('Calendário fictício não pode ser atribuído a dados reais.')
    start, end = iso(meta.get('coverage_start')), iso(meta.get('coverage_end'))
    if start > end:
        raise DataError('Intervalo de cobertura inválido.')
    sessions = meta.get('sessions')
    if not isinstance(sessions, list) or not 2 <= len(sessions) <= 2000:
        raise DataError('Declare entre 2 e 2000 sessões esperadas.')
    sessions = [iso(item) for item in sessions]
    if sessions != sorted(set(sessions)) or sessions[0] < start or sessions[-1] > end:
        raise DataError('Sessões devem ser únicas, ordenadas e dentro da cobertura.')
    if meta['calendar'] == 'synthetic_weekdays':
        if sessions != pd.bdate_range(start, end).strftime('%Y-%m-%d').tolist():
            raise DataError('Sessões incompletas para o calendário fictício declarado.')
    if 'split_demo' in meta:
        event = meta['split_demo']
        if not isinstance(event, dict) or set(event) != {'symbol', 'date', 'ratio'}:
            raise DataError('Metadados do evento fictício inválidos.')
        if event['symbol'] not in assets.symbol.tolist() or iso(event['date']) not in sessions:
            raise DataError('Evento fictício fora da cobertura.')
        ratio = event['ratio']
        if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not np.isfinite(ratio) or ratio <= 0:
            raise DataError('Razão do evento fictício inválida.')
    if not quotes.symbol.isin(assets.symbol).all():
        raise DataError('Cotação referencia ativo desconhecido.')
    quotes['date'] = quotes.date.map(iso)
    if quotes.duplicated(['symbol', 'date']).any():
        raise DataError('Chave de cotação duplicada.')
    expected = pd.MultiIndex.from_product([assets.symbol, sessions], names=['symbol', 'date'])
    actual = pd.MultiIndex.from_frame(quotes[['symbol', 'date']])
    if len(actual) != len(expected) or not actual.difference(expected).empty or not expected.difference(actual).empty:
        raise DataError('A cobertura por ativo/sessão não coincide com a declaração.')
    for column in [*PRICES, 'volume']:
        values = quotes[column]
        if values.map(lambda x: isinstance(x, (bool, np.bool_))).any() or not pd.api.types.is_numeric_dtype(values) or pd.api.types.is_complex_dtype(values):
            raise DataError('Preços e volume devem ter tipos numéricos reais, sem coerção.')
        array = values.to_numpy(dtype=float, na_value=np.nan)
        if not np.isfinite(array).all():
            raise DataError('Preços e volume devem ser completos e finitos.')
        if column == 'volume':
            if ((array < 0) | (array > 1e12) | (array % 1 != 0)).any() or array.sum() > 9e15:
                raise DataError('Volume deve ser inteiro não negativo dentro dos limites.')
            quotes[column] = array.astype('int64')
        else:
            if ((array <= 0) | (array > 1e9)).any():
                raise DataError('Preços devem ser positivos e no máximo um bilhão.')
            quotes[column] = array
    if not ((quotes.low <= quotes[['open', 'close']].min(axis=1)) &
            (quotes.high >= quotes[['open', 'close']].max(axis=1)) & (quotes.low <= quotes.high)).all():
        raise DataError('OHLC incoerente: confira abertura, máxima, mínima e fechamento.')
    return Dataset(assets.sort_values('symbol').reset_index(drop=True),
                   quotes.sort_values(['symbol', 'date']).reset_index(drop=True), meta)

"""Staging por geração e manifesto como ponto único de confirmação."""
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import uuid
from .analytics import analyze, narrative
from .database import build
from .plots import render


def write_json(path, data):
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def publish(dataset, output):
    analysis = analyze(dataset)
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    run_id = uuid.uuid4().hex
    stage = Path(tempfile.mkdtemp(prefix='.pending-', dir=output))
    pointer = output / ('.latest-' + run_id + '.tmp')
    final = output / ('run-' + run_id)
    try:
        analysis.daily.to_csv(stage / 'cotacoes_indicadores.csv', index=False)
        analysis.monthly.to_csv(stage / 'mensal.csv', index=False)
        analysis.summary.to_csv(stage / 'resumo_ativos.csv', index=False)
        analysis.dataset.assets.to_csv(stage / 'ativos.csv', index=False)
        checks = build(stage / 'bolsa.sqlite', analysis)
        info = {'synthetic': analysis.dataset.metadata['synthetic'], 'quotes': len(analysis.daily),
                'assets': len(analysis.dataset.assets), 'sessions': len(analysis.dataset.metadata['sessions']),
                'metadata': analysis.dataset.metadata, 'sql_reconciliation': checks,
                'input_quotes_sha256': hashlib.sha256(analysis.dataset.quotes.to_csv(index=False).encode()).hexdigest(),
                'python': sys.version.split()[0], 'sqlite': sqlite3.sqlite_version,
                'versions': {name: version(name) for name in ('numpy', 'pandas', 'matplotlib')},
                'annualization_sessions': 252, 'volatility_window_returns': 20, 'momentum_window_observations': 21,
                'return_basis': 'price_split_only_no_dividends', 'status': 'complete'}
        write_json(stage / 'validacao.json', info)
        (stage / 'narrativa.txt').write_text(narrative(analysis), encoding='utf-8')
        render(analysis, stage)
        files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()}
        os.replace(stage, final)
        manifest = {'run_id': run_id, 'directory': final.name, 'synthetic': info['synthetic'], 'files_sha256': files}
        write_json(pointer, manifest)
        os.replace(pointer, output / 'latest.json')
        return manifest
    finally:
        if stage.exists():
            shutil.rmtree(stage)
        pointer.unlink(missing_ok=True)

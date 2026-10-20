"""Demonstração offline: não baixa cotações ou acessa contas."""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.local-test/matplotlib'))
sys.path.insert(0, str(ROOT / 'src'))
from bolsa.contracts import DataError
from bolsa.pipeline import publish
from bolsa.synthetic import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs/demo')
    args = parser.parse_args()
    try:
        manifest = publish(generate(), args.output)
    except (DataError, OSError, ValueError, sqlite3.Error):
        print('Demonstração não publicada. Confira contrato, destino e permissões.', file=sys.stderr)
        return 1
    print(json.dumps({'status': 'complete', 'synthetic': True, 'run_id': manifest['run_id']}))
    return 0


if __name__ == '__main__':
    sys.exit(main())

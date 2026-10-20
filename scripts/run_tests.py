"""Executor que registra resultados e rejeita falhas ou testes ignorados."""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.local-test/matplotlib'))
os.environ['PYTHONUTF8'] = '1'
sys.path.insert(0, str(ROOT / 'src'))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
               'skipped': len(result.skipped), 'successful': result.wasSuccessful() and not result.skipped and result.testsRun > 0}
    directory = ROOT / '.local-test'
    directory.mkdir(exist_ok=True)
    (directory / 'tests-result.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary))
    sys.exit(0 if summary['successful'] else 1)

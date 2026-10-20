from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from bolsa.contracts import DataError
from bolsa.database import connect
from bolsa.pipeline import publish
from bolsa.synthetic import generate
from helpers import make

ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'outputs'

    def test_demo_generation_integrity(self):
        manifest = publish(generate(), self.output)
        self.assertEqual(json.loads((self.output / 'latest.json').read_text()), manifest)
        generation = self.output / manifest['directory']
        self.assertEqual(len(manifest['files_sha256']), 9)
        for name, sha in manifest['files_sha256'].items():
            self.assertEqual(hashlib.sha256((generation / name).read_bytes()).hexdigest(), sha)
        checks = json.loads((generation / 'validacao.json').read_text(encoding='utf-8'))
        self.assertTrue(checks['synthetic'])
        self.assertEqual(checks['sql_reconciliation']['status'], 'passed')
        with closing(connect(generation / 'bolsa.sqlite')) as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM fato_cotacao').fetchone()[0], checks['quotes'])

    def test_short_series_can_publish_without_monthly_return(self):
        manifest = publish(make(), self.output)
        self.assertTrue((self.output / manifest['directory'] / 'retornos_mensais.png').exists())

    def test_bad_data_leaves_previous_generation(self):
        first = publish(make(), self.output)
        bad = make()
        bad.quotes.loc[0, 'low'] = 500
        with self.assertRaises(DataError): publish(bad, self.output)
        self.assertEqual(json.loads((self.output / 'latest.json').read_text()), first)

    def test_sql_failure_leaves_previous_generation(self):
        first = publish(make(), self.output)
        with patch('bolsa.pipeline.build', side_effect=DataError('fake')):
            with self.assertRaises(DataError): publish(make(), self.output)
        self.assertEqual(json.loads((self.output / 'latest.json').read_text()), first)
        self.assertFalse(list(self.output.glob('.pending-*')))

    def test_plot_failure_leaves_previous_generation(self):
        first = publish(make(), self.output)
        with patch('bolsa.pipeline.render', side_effect=OSError('fake')):
            with self.assertRaises(OSError): publish(make(), self.output)
        self.assertEqual(json.loads((self.output / 'latest.json').read_text()), first)

    def test_manifest_failure_leaves_previous_generation(self):
        first = publish(make(), self.output)
        original = os.replace
        def replace(source, destination):
            if Path(destination).name == 'latest.json': raise OSError('fake')
            return original(source, destination)
        with patch('bolsa.pipeline.os.replace', side_effect=replace):
            with self.assertRaises(OSError): publish(make(), self.output)
        self.assertEqual(json.loads((self.output / 'latest.json').read_text()), first)
        self.assertFalse(list(self.output.glob('.latest-*.tmp')))

    def test_cli_outside_repository(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_demo.py'), '--output', str(self.output)],
                                cwd=self.temp.name, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['synthetic'])

    def test_cli_failure_sanitized(self):
        blocked = Path(self.temp.name) / 'private-name'
        blocked.write_text('not a directory')
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_demo.py'), '--output', str(blocked)],
                                capture_output=True, text=True, timeout=120)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('private-name', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

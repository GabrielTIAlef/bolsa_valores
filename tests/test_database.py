from contextlib import closing
import sqlite3
import tempfile
from pathlib import Path
import unittest
from bolsa.analytics import analyze
from bolsa.database import build, connect, initialize, load_snapshot, reconcile
from bolsa.contracts import DataError
from helpers import make


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.connection = connect(':memory:')
        self.addCleanup(self.connection.close)
        initialize(self.connection)
        self.data = make(second=True)
        load_snapshot(self.connection, self.data)

    def test_foreign_keys_enabled(self):
        self.assertEqual(self.connection.execute('PRAGMA foreign_keys').fetchone()[0], 1)

    def test_unknown_asset_rejected_by_sql(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.connection:
                self.connection.execute("INSERT INTO fato_cotacao VALUES ('OTHER', '2024-01-01', 100, 101, 99, 100, 100, 1)")

    def test_unknown_date_rejected_by_sql(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.connection:
                self.connection.execute("INSERT INTO fato_cotacao VALUES ('TEST_A', '2030-01-01', 100, 101, 99, 100, 100, 1)")

    def test_duplicate_quote_rejected_by_sql(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.connection:
                self.connection.execute('INSERT INTO fato_cotacao SELECT * FROM fato_cotacao LIMIT 1')

    def test_ohlc_constraints_enforced_by_sql(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.connection:
                self.connection.execute('UPDATE fato_cotacao SET low = high + 1')

    def test_volume_constraints_enforced_by_sql(self):
        for value in (-1, .5):
            with self.subTest(value=value):
                with self.assertRaises(sqlite3.IntegrityError):
                    with self.connection:
                        self.connection.execute('UPDATE fato_cotacao SET volume = ?', (value,))

    def test_repeat_snapshot_no_duplicates(self):
        load_snapshot(self.connection, self.data)
        self.assertEqual(self.connection.execute('SELECT COUNT(*) FROM fato_cotacao').fetchone()[0], 6)
        self.assertEqual(self.connection.execute('SELECT SUM(volume) FROM fato_cotacao').fetchone()[0], 903)

    def test_sql_failure_rolls_back_previous_snapshot(self):
        before = self.connection.execute('SELECT * FROM fato_cotacao ORDER BY symbol, date').fetchall()
        self.connection.execute("CREATE TRIGGER reject_b BEFORE INSERT ON fato_cotacao WHEN NEW.symbol = 'TEST_B' BEGIN SELECT RAISE(ABORT, 'fake failure'); END")
        changed = make((200., 210., 199.), second=True)
        with self.assertRaises(sqlite3.IntegrityError): load_snapshot(self.connection, changed)
        self.assertEqual(before, self.connection.execute('SELECT * FROM fato_cotacao ORDER BY symbol, date').fetchall())
        self.assertFalse(self.connection.execute('PRAGMA foreign_key_check').fetchall())

    def test_monthly_sql_python_reconcile(self):
        data = make((100., 120., 120., 120.), dates=['2024-01-02', '2024-01-31', '2024-02-01', '2024-02-29'], second=True)
        load_snapshot(self.connection, data)
        result = reconcile(self.connection, analyze(data))
        self.assertEqual(result['monthly_rows'], 4)
        row = self.connection.execute("SELECT return_monthly_price, mean_close_mom FROM vw_mensal_retorno WHERE symbol='TEST_A' AND month='2024-02'").fetchone()
        self.assertAlmostEqual(row[0], 0)
        self.assertAlmostEqual(row[1], 120 / 110 - 1)

    def test_month_gap_sql_return_null(self):
        data = make((100., 110.), dates=['2024-01-31', '2024-03-28'])
        load_snapshot(self.connection, data)
        reconcile(self.connection, analyze(data))
        self.assertTrue(all(row[0] is None for row in self.connection.execute('SELECT return_monthly_price FROM vw_mensal_retorno')))

    def test_build_closes_file_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.sqlite'
            build(path, analyze(self.data))
            moved = path.with_name('moved.sqlite')
            path.rename(moved)
            with self.assertRaises(DataError): build(moved, analyze(self.data))

    def test_disabled_foreign_keys_not_accepted(self):
        self.connection.execute('PRAGMA foreign_keys=OFF')
        with self.assertRaises(DataError): load_snapshot(self.connection, self.data)

    def test_reconciliation_catches_changed_sql_data(self):
        with self.connection:
            self.connection.execute('UPDATE fato_cotacao SET volume = volume + 1')
        with self.assertRaises(DataError): reconcile(self.connection, analyze(self.data))

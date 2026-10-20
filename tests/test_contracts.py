import copy
import unittest
import numpy as np
from pandas.testing import assert_frame_equal
from bolsa.contracts import DataError, Dataset, validate
from bolsa.synthetic import generate
from helpers import make


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.data = make()

    def test_generator_deterministic_and_complete(self):
        a, b = generate(), generate()
        assert_frame_equal(a.quotes, b.quotes)
        result = validate(a)
        self.assertEqual(len(result.assets), 6)
        self.assertEqual(len(result.quotes), len(a.metadata['sessions']) * 6)

    def test_validation_does_not_mutate(self):
        before = copy.deepcopy(self.data)
        validate(self.data)
        assert_frame_equal(before.quotes, self.data.quotes)
        self.assertEqual(before.metadata, self.data.metadata)

    def test_duplicate_keys_rejected(self):
        self.data.quotes.loc[1, 'date'] = self.data.quotes.loc[0, 'date']
        with self.assertRaises(DataError): validate(self.data)

    def test_unknown_asset_rejected(self):
        self.data.quotes.loc[0, 'symbol'] = 'OTHER'
        with self.assertRaises(DataError): validate(self.data)

    def test_duplicate_asset_rejected(self):
        import pandas as pd
        self.data.assets = pd.concat([self.data.assets, self.data.assets])
        with self.assertRaises(DataError): validate(self.data)

    def test_missing_observation_rejected(self):
        self.data.quotes = self.data.quotes.iloc[:-1]
        with self.assertRaises(DataError): validate(self.data)

    def test_common_missing_session_rejected_in_synthetic_calendar(self):
        data = generate()
        missing = data.metadata['sessions'][20]
        data.metadata['sessions'].remove(missing)
        data.quotes = data.quotes.loc[data.quotes.date.ne(missing)]
        with self.assertRaises(DataError): validate(data)

    def test_dates_must_be_iso_and_real(self):
        for value in ('01/01/2024', '2024-02-30', '2024-01-01T00:00:00', None):
            with self.subTest(value=value):
                data = make()
                data.quotes.loc[0, 'date'] = value
                with self.assertRaises(DataError): validate(data)

    def test_price_must_be_positive_finite_real(self):
        for value in (0., -1., np.inf, np.nan, 1e10):
            with self.subTest(value=value):
                data = make()
                data.quotes.loc[0, 'adjusted_close'] = value
                with self.assertRaises(DataError): validate(data)

    def test_complex_and_boolean_prices_rejected(self):
        for value in (True, 100 + 1j):
            with self.subTest(value=value):
                data = make()
                data.quotes['adjusted_close'] = value
                with self.assertRaises(DataError): validate(data)

    def test_string_price_not_coerced(self):
        self.data.quotes['adjusted_close'] = self.data.quotes.adjusted_close.astype(str)
        with self.assertRaises(DataError): validate(self.data)

    def test_volume_constraints(self):
        for value in (-1., .5, np.inf, np.nan, 1e13, True):
            with self.subTest(value=value):
                data = make()
                data.quotes['volume'] = value
                with self.assertRaises(DataError): validate(data)

    def test_incoherent_ohlc_rejected(self):
        for column, value in (('low', 200.), ('high', 50.), ('open', 500.)):
            with self.subTest(column=column):
                data = make()
                data.quotes.loc[0, column] = value
                with self.assertRaises(DataError): validate(data)

    def test_mixed_currency_rejected(self):
        self.data.assets['currency'] = 'BRL'
        with self.assertRaises(DataError): validate(self.data)

    def test_missing_policy_rejected(self):
        del self.data.metadata['adjustment_basis']
        with self.assertRaises(DataError): validate(self.data)

    def test_total_return_not_silently_assumed(self):
        self.data.metadata['adjustment_basis'] = 'total_return'
        with self.assertRaises(DataError): validate(self.data)

    def test_synthetic_calendar_not_allowed_for_real_origin(self):
        data = generate()
        data.metadata['synthetic'] = False
        with self.assertRaises(DataError): validate(data)

    def test_formula_symbol_and_name_rejected(self):
        for column, value in (('symbol', '=ABC'), ('name', '-formula')):
            with self.subTest(column=column):
                data = make()
                data.assets.loc[0, column] = value
                with self.assertRaises(DataError): validate(data)

    def test_unordered_or_duplicate_sessions_rejected(self):
        for sessions in (list(reversed(self.data.metadata['sessions'])), self.data.metadata['sessions'] * 2):
            self.data.metadata['sessions'] = sessions
            with self.assertRaises(DataError): validate(self.data)

    def test_extra_column_rejected(self):
        self.data.quotes['customer_name'] = 'private'
        with self.assertRaises(DataError): validate(self.data)

    def test_empty_input_rejected(self):
        self.data.quotes = self.data.quotes.iloc[:0]
        with self.assertRaises(DataError): validate(self.data)

    def test_non_table_input_rejected(self):
        with self.assertRaises(DataError): validate(Dataset(None, None, {}))

    def test_unknown_metadata_not_exported(self):
        self.data.metadata['api_token'] = 'invented-not-a-secret'
        with self.assertRaises(DataError): validate(self.data)

    def test_reversed_coverage_rejected(self):
        self.data.metadata['coverage_start'] = '2025-01-01'
        with self.assertRaises(DataError): validate(self.data)

    def test_dates_outside_supported_range_rejected(self):
        self.data.metadata['coverage_end'] = '9999-12-31'
        with self.assertRaises(DataError): validate(self.data)

    def test_invalid_split_metadata_rejected(self):
        for event in ({'symbol': 'OTHER', 'date': '2024-01-01', 'ratio': 2},
                      {'symbol': 'TEST_A', 'date': '2024-01-01', 'ratio': -1}):
            with self.subTest(event=event):
                self.data.metadata['split_demo'] = event
                with self.assertRaises(DataError): validate(self.data)

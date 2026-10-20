import unittest
import numpy as np
from pandas.testing import assert_frame_equal
from bolsa.analytics import analyze, narrative
from helpers import make


class AnalyticsTests(unittest.TestCase):
    def test_known_returns_compound_not_sum(self):
        result = analyze(make())
        self.assertTrue(np.isnan(result.daily.return_daily.iloc[0]))
        np.testing.assert_allclose(result.daily.return_daily.iloc[1:], [.1, -.1])
        self.assertAlmostEqual(result.summary.return_window_price.iloc[0], -.01)
        self.assertAlmostEqual((1 + result.daily.return_daily.dropna()).prod() - 1, -.01)
        self.assertNotAlmostEqual(result.summary.return_window_price.iloc[0], result.daily.return_daily.sum())

    def test_base_100_and_drawdown_known(self):
        result = analyze(make((100., 120., 90., 108.)))
        np.testing.assert_allclose(result.daily.base_100, [100, 120, 90, 108])
        np.testing.assert_allclose(result.daily.drawdown, [0, 0, -.25, -.1])
        self.assertAlmostEqual(result.summary.max_drawdown.iloc[0], -.25)

    def test_no_cross_asset_return_or_window(self):
        result = analyze(make(second=True))
        second = result.daily.query("symbol == 'TEST_B'")
        self.assertTrue(np.isnan(second.return_daily.iloc[0]))
        np.testing.assert_allclose(second.return_daily.iloc[1:], 0)
        self.assertTrue(second.momentum_21.isna().all())
        self.assertTrue(second.volatility_20_annualized.isna().all())

    def test_sort_before_calculation(self):
        data = make()
        expected = analyze(data).daily
        data.quotes = data.quotes.iloc[::-1]
        assert_frame_equal(analyze(data).daily, expected)

    def test_sample_volatility_uses_ddof_one(self):
        result = analyze(make())
        self.assertAlmostEqual(result.summary.volatility_annualized.iloc[0], np.std([.1, -.1], ddof=1) * np.sqrt(252))

    def test_insufficient_volatility_absent(self):
        result = analyze(make((100., 110.)))
        self.assertTrue(np.isnan(result.summary.volatility_annualized.iloc[0]))

    def test_rolling_requires_twenty_returns(self):
        prices = 100 * np.cumprod(1 + np.linspace(-.01, .02, 22))
        result = analyze(make(prices))
        self.assertTrue(result.daily.volatility_20_annualized.iloc[:20].isna().all())
        self.assertTrue(np.isfinite(result.daily.volatility_20_annualized.iloc[20]))
        expected = result.daily.return_daily.iloc[1:21].std(ddof=1) * np.sqrt(252)
        self.assertAlmostEqual(result.daily.volatility_20_annualized.iloc[20], expected)

    def test_momentum_requires_twenty_one_lags(self):
        result = analyze(make(np.arange(100., 123.)))
        self.assertTrue(result.daily.momentum_21.iloc[:21].isna().all())
        self.assertAlmostEqual(result.daily.momentum_21.iloc[21], .21)

    def test_split_does_not_create_artificial_adjusted_loss(self):
        result = analyze(make((50., 50., 51.), raw=(100., 50., 51.)))
        self.assertAlmostEqual(result.daily.return_daily.iloc[1], 0)
        self.assertAlmostEqual(result.daily.close.iloc[1] / result.daily.close.iloc[0] - 1, -.5)

    def test_monthly_mean_variation_not_return(self):
        data = make((100., 120., 120., 120.), dates=['2024-01-02', '2024-01-31', '2024-02-01', '2024-02-29'])
        result = analyze(data).monthly
        self.assertTrue(np.isnan(result.return_monthly_price.iloc[0]))
        self.assertAlmostEqual(result.return_monthly_price.iloc[1], 0)
        self.assertAlmostEqual(result.mean_close_mom.iloc[1], 120 / 110 - 1)

    def test_month_gap_not_treated_as_one_month(self):
        data = make((100., 110.), dates=['2024-01-31', '2024-03-28'])
        result = analyze(data).monthly
        self.assertTrue(result.return_monthly_price.isna().all())
        self.assertTrue(result.mean_close_mom.isna().all())

    def test_partial_month_is_flagged(self):
        data = make((100., 110., 120.), dates=['2024-01-02', '2024-01-31', '2024-02-15'])
        result = analyze(data).monthly
        self.assertFalse(result.period_complete_declared.any())
        self.assertFalse(result.return_periods_complete_declared.any())

    def test_volume_reconciliation(self):
        result = analyze(make(second=True))
        self.assertEqual(result.monthly.volume.sum(), result.daily.volume.sum())
        self.assertEqual(result.summary.volume.sum(), result.daily.volume.sum())

    def test_narrative_is_descriptive_and_reconciles(self):
        result = analyze(make())
        text = narrative(result)
        self.assertIn('TEST_A: 3 observações', text)
        self.assertIn('-1.00%', text)
        self.assertIn('303 ações', text)
        self.assertIn('não inclui dividendos', text)

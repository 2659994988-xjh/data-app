"""Small checks for the business definitions, not UI implementation details."""

import unittest

import pandas as pd

from delivery_metrics import analysis_orders, load_orders, summary, weekly_rates


class DeliveryMetricsTest(unittest.TestCase):
    def test_date_level_lateness_and_eligible_denominator(self):
        rows = pd.DataFrame(
            [
                ("a", "SP", "delivered", "2018-01-01", "2018-01-02", "2018-01-03 23:59:00", "2018-01-03"),
                ("b", "SP", "delivered", "2018-01-01", "2018-01-02", "2018-01-04 00:01:00", "2018-01-03"),
                ("c", "RJ", "shipped", "2018-01-01", "2018-01-02", None, "2018-01-03"),
                ("d", "RJ", "delivered", "2018-01-01", "2018-01-02", None, "2018-01-03"),
            ],
            columns=[
                "order_id", "customer_state", "order_status", "order_purchase_timestamp",
                "order_delivered_carrier_date", "order_delivered_customer_date",
                "order_estimated_delivery_date",
            ],
        )
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "orders.csv"
            rows.to_csv(path, index=False)
            result = analysis_orders(load_orders(path))

        self.assertEqual(summary(result)["orders"], 2)
        self.assertEqual(summary(result)["late_orders"], 1)
        self.assertEqual(summary(result)["late_rate"], 0.5)
        self.assertEqual(summary(result)["median_late_days"], 1.0)
        self.assertEqual(weekly_rates(result)["orders"].sum(), 2)


if __name__ == "__main__":
    unittest.main()

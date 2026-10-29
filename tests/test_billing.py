"""Billing shape: monthly plans get a 14-day trial, one-time plans check out with mode=payment."""

import pathlib
import tempfile
import unittest

from ai_profile_karma import web


def _billing(tmp, prices, one_time=""):
    env = {
        "STRIPE_SECRET_KEY": "sk_test_x",
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "STRIPE_PRICES": prices,
        "STRIPE_ONE_TIME_PLANS": one_time,
        "PUBLIC_URL": "https://example.test",
    }
    srv = web.make_server("127.0.0.1", 0, pathlib.Path(tmp), env=env)
    return srv.RequestHandlerClass.billing


class TestBillingShape(unittest.TestCase):
    def test_monthly_checkout_carries_14_day_trial(self):
        with tempfile.TemporaryDirectory() as t:
            billing = _billing(t, "personal=price_123,family=price_456")
            sent = {}
            billing._stripe = lambda path, form: sent.update(form) or {"url": "https://checkout.test/s"}
            self.assertEqual(billing.checkout("personal"), "https://checkout.test/s")
            self.assertEqual(sent["mode"], "subscription")
            self.assertEqual(sent["line_items[0][price]"], "price_123")
            self.assertEqual(sent["subscription_data[trial_period_days]"], "14")

    def test_one_time_checkout_uses_payment_mode_without_trial(self):
        with tempfile.TemporaryDirectory() as t:
            billing = _billing(t, "personal=price_123,lifetime=price_789", one_time="lifetime")
            sent = {}
            billing._stripe = lambda path, form: sent.update(form) or {"url": "https://checkout.test/s"}
            self.assertEqual(billing.checkout("lifetime"), "https://checkout.test/s")
            self.assertEqual(sent["mode"], "payment")
            self.assertEqual(sent["line_items[0][price]"], "price_789")
            self.assertNotIn("subscription_data[trial_period_days]", sent)

    def test_pricing_page_notes_trial_on_monthly_plans(self):
        with tempfile.TemporaryDirectory() as t:
            billing = _billing(t, "personal=price_123,lifetime=price_789", one_time="lifetime")
            page = web.pricing_page(billing)
            self.assertIn("14-day free trial", page)
            self.assertIn("one-time plans do not", page)


if __name__ == "__main__":
    unittest.main()

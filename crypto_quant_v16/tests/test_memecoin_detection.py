import unittest
from crypto_quant_v16.memecoin_alpha.memecoin_detection import MemecoinDetectionSystem

class TestMemecoinDetectionSystem(unittest.TestCase):
    def setUp(self):
        self.detector = MemecoinDetectionSystem()

    def test_generate_token_report(self):
        report = self.detector.generate_token_report()
        self.assertIsInstance(report, dict)
        # Au moins 0 ou plus tokens détectés
        for token, info in report.items():
            self.assertIn('hype_score', info)
            self.assertIn('whale_activity', info)
            self.assertIn('rug_risk', info)

    def test_generate_token_report_extended(self):
        report = self.detector.generate_token_report_extended()
        self.assertIsInstance(report, dict)
        for token, info in report.items():
            self.assertIn('hype_score_social', info)
            self.assertIn('hype_score_twitter', info)
            self.assertIn('hype_score_reddit', info)
            self.assertIn('whale_activity', info)
            self.assertIn('rug_risk', info)
            self.assertIn('contract_status', info)

    def test_alerts(self):
        # Doit pouvoir envoyer une alerte sans erreur
        self.detector.send_real_time_alert('TOKEN_TEST', 'TEST_ALERT', 0.99)

if __name__ == '__main__':
    unittest.main()

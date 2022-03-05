import unittest
from metric_calculator import MetricCalculator

class MetricCalculatorTest(unittest.TestCase):
  def setUp(self):
    gold_standard_root_path = './awr/results'
    self.metric_calculator = MetricCalculator()

  def test_should_fetch_gold_standard_by_name(self):
    self.metric_calculator.fetch_gold_standard('joinha')
    self.assertTrue(True)

  def test_should_calculate_distance_from_origin(self):
    self.metric_calculator.fetch_gold_standard('prensão palmar')

if __name__ == '__main__':
  unittest.main()
import unittest
import numpy as np
from metric_calculator import MetricCalculator
import os

class EuclideanDistanceUnitTests(unittest.TestCase):
  def setUp(self):
    self.metric_calculator = MetricCalculator('', '')

  def test_should_return_zero_for_euclidean_distance_of_same_points(self):
    point_a = [1, 2, 3]
    point_b = [1, 2, 3]

    distance = self.metric_calculator.calculate_euclidean_distance(point_a, point_b)
    self.assertEqual(distance, 0)

  def test_should_calculate_euclidian_distance_from_origin(self):
    point_a = [0, 0, 0]
    point_b = [3, 4, 0]

    distance = self.metric_calculator.calculate_euclidean_distance(point_a, point_b)
    self.assertEqual(distance, 5)

class MeanPerJointPositionErrorUnitTests(unittest.TestCase):
  def setUp(self):
    self.metric_calculator = MetricCalculator('', '')

  def test_should_calculate_mpjpe_for_one_joint(self):
    gold_std_joints =  [[0.0, 0.0, 0.0]]
    comparison_joint = [[3.0, 4.0, 0.0]]

    mpjpe = self.metric_calculator.calculate_mean_per_joint_position_error(gold_std_joints, comparison_joint)

    self.assertEqual(mpjpe, 5)

  def test_should_calculate_mpjpe_for_multiple_joints(self):
    gold_std_joints =  [
      [0.0, 0.0, 0.0],
      [1.0, 2.0, 0.0]
    ]
    comparison_joint = [
      [3.0, 4.0, 0.0],
      [6.0, 14.0, 0.0]
    ]

    mpjpe = self.metric_calculator.calculate_mean_per_joint_position_error(gold_std_joints, comparison_joint)

    self.assertEqual(mpjpe, 9)

class TransformJointShapeUnitTests(unittest.TestCase):
  def setUp(self):
    self.metric_calculator = MetricCalculator('', '')

  def test_should_transform_joint_matrix_with_two_joints(self):
    joints = [
      [1, 2, 3,  4, 5, 6]
    ]
    total_joints = 2

    transformed = self.metric_calculator.transform_joint(joints, total_joints)

    expected_matrix = [
      [1, 2, 3],
      [4, 5, 6]
    ]

    np.testing.assert_array_equal(transformed, expected_matrix)

  def test_should_transform_joint_matrix_with_14_joints(self):
    joints = [
      [
        1, 2, 3,     4, 5, 6,    
        7, 8, 9,     10, 11, 12,
        13, 14, 15,  16, 17, 18,  
        19, 20, 21,  22, 23, 24,
        25, 26, 27,  28, 29, 30,  
        31, 32, 33,  34, 35, 36,
        37, 38, 39,  40, 41, 42
      ]
    ]
    total_joints = 14

    transformed = self.metric_calculator.transform_joint(joints, total_joints)

    expected_matrix = [
      [1, 2, 3],
      [4, 5, 6],
      [7, 8, 9],
      [10, 11, 12],
      [13, 14, 15],
      [16, 17, 18],
      [19, 20, 21],
      [22, 23, 24],
      [25, 26, 27],
      [28, 29, 30],
      [31, 32, 33],
      [34, 35, 36],
      [37, 38, 39],
      [40, 41, 42]
    ]

    np.testing.assert_array_equal(transformed, expected_matrix)
    
class ReadFileUnitTests(unittest.TestCase):
  def setUp(self):
    self.file_content = [
      [1.0, 2.0, 3.0],
      [4.0, 5.0, 6.0]
    ]
    self.file_name = 'test_file.txt'

    np.savetxt(self.file_name, self.file_content)

    self.metric_calculator = MetricCalculator('', '')

  def tearDown(self):
    os.remove(self.file_name)
    
  def test_should_read_file_content(self):
    path = self.file_name
    content_red = self.metric_calculator.read_file(path)

    expected_content = self.file_content
    np.testing.assert_array_equal(content_red, expected_content)

class FetchJointsUnitTests(unittest.TestCase):
  def setUp(self):
    self.file_content = [
      [1.0, 2.0, 3.0],
      [4.0, 5.0, 6.0]
    ]
    
    self.comparison_file_content = [
      [7.0, 8.0, 9.0],
      [1.0, 2.0, 3.0]
    ]

    self.folder = 'test_folder'
    self.date = '2022-08-03'
    os.makedirs(f'{self.folder}/{self.date}')
    
    self.file_name = 'palmar_grasp.txt'
    self.file_path = f'{self.folder}/{self.file_name}'

    np.savetxt(self.file_path, self.file_content, fmt='%.1f')

    self.comparison_file_name = 'palmar_grasp.txt'
    self.comparison_file_path = f'{self.folder}/{self.date}/{self.comparison_file_name}'

    np.savetxt(self.comparison_file_path, self.comparison_file_content, fmt='%.1f')

    self.metric_calculator = MetricCalculator('', '')

  def tearDown(self):
    os.remove(self.file_path)
    os.remove(self.comparison_file_path)
    os.removedirs(f'{self.folder}/{self.date}')
    
  def test_should_fetch_gold_standard_joint_file(self):
    root = self.folder
    grasp_name = self.file_name
    content_red = self.metric_calculator.fetch_joints(root, grasp_name, None)

    expected_content = self.file_content
    np.testing.assert_array_equal(content_red, expected_content)

  def test_should_fetch_comparison_joint_file(self):
    root = self.folder
    grasp_name = self.file_name
    date = self.date
    content_red = self.metric_calculator.fetch_joints(root, grasp_name, date)

    expected_content = self.comparison_file_content
    np.testing.assert_array_equal(content_red, expected_content)

class MetricCalculatorFunctionalTests(unittest.TestCase):
  def setUp(self):
    gold_standard_root_path = './awr/prediction/gold_standard'
    comparison_root_path = './awr/prediction/follow_up/'
    self.metric_calculator = MetricCalculator(gold_standard_root_path, comparison_root_path)


if __name__ == '__main__':
  unittest.main()
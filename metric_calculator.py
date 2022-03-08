import numpy as np
import math

class MetricCalculator:
  def __init__(self, gold_standard_root_path, comparison_root_path):
    self.gold_standard_root_path = gold_standard_root_path
    self.comparison_root_path = comparison_root_path
    self.gold_standard = {}

  def calculate_metrics(self, grasp_name: str, date: str, total_joints: int):
    """
      grasp_name: string
      date: string (e.g: '2022-03-08')
      total_joints: int (default: 14)
    """
    gold_std_joints = self.fetch_joints(self.gold_standard_root_path, grasp_name, None)
    comparison_joints = self.fetch_joints(self.comparison_root_path, grasp_name, date)
    
    gold_t = self.transform_joint(gold_std_joints, total_joints)
    comparison_t = self.transform_joint(comparison_joints, total_joints)
    
    mean_per_joint_error = self.calculate_mean_per_joint_position_error(gold_t, comparison_t)
    
    return mean_per_joint_error

  def fetch_joints(self, root_path, grasp_name, date):
    full_path =  f'{root_path}/{grasp_name}' if date is None else f'{root_path}/{date}/{grasp_name}'

    return self.read_file(full_path)

  def read_file(self, path):
    return np.loadtxt(path)

  def transform_joint(self, joint_matrix, total_joints):
    joints_shape = (total_joints, 3)

    return np.reshape(joint_matrix, joints_shape)

  def calculate_mean_per_joint_position_error(self, gold_std_joints, comparison_joints):
    """
      gold_std_joints: (total_joints x 3)
      comparison_joints: (total_joints x 3)
    """
    distances = []
    
    for row, comparison_joint in enumerate(gold_std_joints):
      gold_std_joint = comparison_joints[row]

      distance = self.calculate_euclidean_distance(comparison_joint, gold_std_joint)
      distances.append(distance)
    
    return np.mean(distances)

  def calculate_euclidean_distance(self, point_a: list, point_b: list):
    """
      params:
        point_a: tuple (x, y, z)
        point_b: tuple (x, y, z)
      returns:
        distance: number
    """
    x1, y1, z1 = point_a
    x2, y2, z2 = point_b

    square_distance = (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2

    return  math.sqrt(square_distance)


import numpy as np
import time
import math
import cv2
import os
from datetime import datetime
from pathlib import Path
import requests
from argparse import ArgumentParser
from metric_calculator import MetricCalculator
from dotenv import load_dotenv
import traceback

load_dotenv()

class ExperimentRunner:
  def __init__(self):
    import pyrealsense2 as rs

    self.rs = rs
    self.is_left_hand = False

    self.camera_config = {
      'width': 640,
      'height': 480,
      'frame_rate': 60
    }

    self.experiment_sequence = {
      'light': [2]
    }

    self.parameters = {
      'patient_name': '',
      'light_setup': 'luz-na-cam', # luz-na-cam | luz-de-lado | luz-na-mao
      'distance': 28, # 28 | 35 | 37,
      'type': 'gold_standard', # gold_standard | follow_up,
      'repetitions': 1, # 1 | 10
      'hand_side': 'esquerda' # esquerda | direita
    }

    self.reps_counter = 0

    self.keys = {
      'Enter': 13,
      'Esc': 27,
      'Yes': ord('s'),
      'No': ord('n')
    }

    self.colors = {
      'green': (0, 255, 0),
      'red': (0, 0, 255)
    }

    self.grasp_iterator = 0
    self.follow_up_grasps = [
      'fechada',
      'semiaberta 1',
      'semiaberta 2',
      'aberta'
    ]

    self.clipping_distance = None

    # Camera resources
    self.pipeline = None
    self.profile = None
    self.align_processor = None

    self.stop_main_loop_flag = False
    self.force_exit = False

  def set_params(self, patient_name, light_setup, distance, type, repetitions, hand_side):
    self.parameters['patient_name'] = patient_name
    self.parameters['light_setup'] = light_setup
    self.parameters['distance'] = distance
    self.parameters['type'] = type
    self.parameters['repetitions'] = repetitions
    self.parameters['hand_side'] = hand_side

    self.reps_counter = 0
    self.grasp_iterator = 0
    self.stop_main_loop_flag = False

  def start(self):
    self.config_cam()
    return self.start_main_loop()

  def config_cam(self):
    self.enable_depth_and_rgb_streams()
    self.config_clipping_distance()
    self.create_align_processor()

  def enable_depth_and_rgb_streams(self):
    self.pipeline = self.rs.pipeline()
    realsense_config = self.rs.config()

    width = self.camera_config['width']
    height = self.camera_config['height']
    frame_rate = self.camera_config['frame_rate']

    realsense_config.enable_stream(self.rs.stream.depth, width, height, self.rs.format.z16, frame_rate)
    realsense_config.enable_stream(self.rs.stream.color, width, height, self.rs.format.bgr8, frame_rate)

    self.profile = self.pipeline.start(realsense_config)

  def config_clipping_distance(self):
    depth_sensor = self.profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    print("Depth Scale is: ", depth_scale)

    clipping_distance_in_meters = 0.40
    self.clipping_distance = clipping_distance_in_meters / depth_scale

    print('clipping_distance', self.clipping_distance)

  def create_align_processor(self):
    color_stream = self.rs.stream.color
    self.align_processor = self.rs.align(color_stream)

  def start_main_loop(self):
    print(f'starting main loop, flag: {self.stop_main_loop_flag}')
    while self.stop_main_loop_flag == False:
      try:
        self.process_frames()
      except Exception as exception:
        print('Error during processing')
        traceback.print_exc()
        print('Ocorreu um erro, gostaria de continuar?')
        key = input('Pressione: (s) - Sim / (n) - Não\n> ')
        
        self.stop_main_loop_flag = (key == 'n')
    
    self.pipeline.stop()
    self.stop()
    return self.force_exit

  def process_frames(self):
    frames = self.pipeline.wait_for_frames()
    aligned_frames = self.align_processor.process(frames)

    depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()

    cv2.imshow('rgb', np.asanyarray(color_frame.get_data()))

    if not depth_frame or not color_frame:
      return

    filtered_depth_frame = self.filter_depth_frame(depth_frame)
    color_frame_without_background = self.remove_background_from_color_frame(color_frame, depth_frame)
    centroid = self.calculate_centroid(depth_frame)

    if not centroid:
      centroid = (0,0,0)
    
    color_frame_with_centroid = self.draw_centroid(centroid, color_frame_without_background.copy())
    color_frame_with_distance = self.draw_centroid_distance(centroid, color_frame_with_centroid.copy())
    color_frame_full_ui = self.draw_user_data(color_frame_with_distance.copy())

    depth_colormap = self.colorize_depth_frame(filtered_depth_frame)
    frames = self.join_frames(color_frame_full_ui, depth_colormap)

    self.show_frames(frames)

    key_pressed = cv2.waitKey(1)
    self.check_exit_pressed(key_pressed)
    
    if key_pressed == self.keys['Enter']:
      print('Will capture frame')
      self.save_frames(
        color_frame,
        color_frame_without_background,
        color_frame_with_distance,
        color_frame_full_ui,
        np.asanyarray(filtered_depth_frame.get_data()),
        centroid
      )

      if self.parameters['type'] == 'follow_up':
        self.grasp_iterator += 1

        if self.grasp_iterator == len(self.follow_up_grasps):
          self.grasp_iterator = 0
          self.reps_counter += 1
      else:
        self.reps_counter += 1

      if self.reps_counter == self.parameters['repetitions']:
        self.stop_main_loop_flag = True

  def filter_depth_frame(self, depth_frame):
    spatial = self.rs.spatial_filter()
    spatial.set_option(self.rs.option.filter_magnitude, 5)
    spatial.set_option(self.rs.option.filter_smooth_alpha, 1)
    spatial.set_option(self.rs.option.filter_smooth_delta, 50)
    
    hole_filling = self.rs.hole_filling_filter()
    
    filtered_depth = spatial.process(depth_frame)
    filled_depth = hole_filling.process(filtered_depth)

    return filled_depth

  def remove_background_from_color_frame(self, color_frame, depth_frame):
    depth_matrix = np.asanyarray(depth_frame.get_data())
    color_matrix = np.asanyarray(color_frame.get_data())

    background_color = 0

    depth_image_3d = np.dstack((depth_matrix, depth_matrix, depth_matrix))
    rgb_without_background = np.where(
      (depth_image_3d > self.clipping_distance) | (depth_image_3d <= 0), 
      background_color, 
      color_matrix
    )

    return rgb_without_background

  def calculate_centroid(self, depth_frame):
    depth_matrix = np.asanyarray(depth_frame.get_data())

    mass_y, mass_x = np.where((depth_matrix > 0) & (depth_matrix < self.clipping_distance))

    if not len(mass_x) or not len(mass_y):
      return

    center_x = math.ceil(np.average(mass_x))
    center_y = math.ceil(np.average(mass_y))
    center_z = depth_frame.get_distance(center_x, center_y)

    # center_in_cm = center_z * 100
    # print('distance in cm: %.2f\r' % center_in_cm, end='\r')

    return center_x, center_y, center_z

  def draw_centroid(self, centroid, color_frame):
    x, y, z = centroid

    color = self.get_text_color(z)

    center_x = round(self.camera_config['width'] / 2)
    center_y = round(self.camera_config['height'] / 2)

    ref_center = (center_x, center_y)

    circle_color = self.get_circle_color(center_x, center_y, x, y)

    color_frame = cv2.circle(color_frame, center=ref_center, radius=10, color=circle_color, thickness=1)
    
    return cv2.circle(color_frame, center=(x, y), radius=2, color=color, thickness=-1)

  def get_circle_color(self, center_x, center_y, x, y):
    radius = 10 / 2
    thresh = radius + 1

    valid_x = (center_x - thresh) < round(x) < (center_x + thresh)
    valid_y = (center_y - thresh) < round(y) < (center_y + thresh)

    return self.colors['green'] if valid_x and valid_y else self.colors['red']

  def get_text_color(self, z):
    is_distance_valid = self.check_is_distance_valid(z)

    color = self.colors['green'] if is_distance_valid else self.colors['red']

    return color

  def check_is_distance_valid(self, z):
    distance_in_cm = z * 100
    expected_distance = self.parameters['distance']
    is_distance_valid = round(distance_in_cm) == expected_distance

    return is_distance_valid

  def draw_centroid_distance(self, centroid, color_frame):
    x, y, z = centroid
    
    color = self.get_text_color(z)
   
    distance_in_cm = z * 100
    distance_formatted = ('%.0f' % distance_in_cm)
    origin = (x + 10, y - 20)

    return cv2.putText(
      color_frame, distance_formatted, origin, cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_8
    )

  def draw_user_data(self, color_frame):
    patient_name = self.parameters['patient_name']
    light_setup = self.parameters['light_setup']
    distance = self.parameters['distance']
    type = self.parameters['type']
    repetitions = self.parameters['repetitions']
    hand_side = self.parameters['hand_side']
    
    ui_volunteer = f'Volunt. {patient_name}'
    ui_setup = f'Luz {light_setup}'
    ui_distance = f'Dist {distance}cm'
    ui_type = 'Padrao Ouro' if type == 'gold_standard' else 'Acompanhamento'
    ui_reps = f'Rep. {self.reps_counter}/{repetitions}'

    grasp = self.follow_up_grasps[self.grasp_iterator] if type == 'follow_up' else 'aberta'
    ui_hand_side = f'Mao {hand_side} {grasp}'
    
    origin1 = (10, 30)
    origin2 = (10, 55)
    origin3 = (10, 80)

    self.write_on_frame(color_frame, f'{ui_volunteer}; {ui_setup}', origin1)
    self.write_on_frame(color_frame, f'{ui_distance}; {ui_type}', origin2)
    self.write_on_frame(color_frame,f'{ui_reps}; {ui_hand_side}', origin3)

    return color_frame

  def write_on_frame(self, frame, text, origin):
    color = (255,255,255)
    fontScale = .8
    thickness = 2

    cv2.putText(
      frame, text, origin, cv2.FONT_HERSHEY_SIMPLEX, fontScale, color, thickness, cv2.LINE_AA
    )

  def colorize_depth_frame(self, depth_frame):
    depth_matrix = np.asanyarray(depth_frame.get_data())
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_matrix, alpha=0.03), cv2.COLORMAP_JET)

    return depth_colormap

  def join_frames(self, color_frame, depth_frame):
    frames = np.hstack((color_frame, depth_frame))

    return frames

  def show_frames(self, frames):
    cv2.namedWindow('exercise-recorder', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('exercise-recorder', self.camera_config['width'] * 2, self.camera_config['height'])
    cv2.imshow('exercise-recorder', frames)

  def check_exit_pressed(self, key_pressed):
    if key_pressed == self.keys['Esc']:
      print('Application will terminate!')
      self.stop_main_loop_flag = True
      self.force_exit = True
    elif key_pressed != -1:
      print(f'Entrada não reconhecida: "{key_pressed}"')

  def save_frames(self, rgb_frame, rgb_frame_without_bg, rgb_frame_with_distance, rgb_frame_ui, depth_frame, centroid):
    color_frame = np.asanyarray(rgb_frame.get_data())
    path = self.build_path()

    rgb_full_frame_path = os.path.join(path, 'rgb_full_frame.png')
    cv2.imwrite(rgb_full_frame_path, color_frame)

    rgb_filtered_frame_no_ui_path = os.path.join(path, 'rgb_filtered_frame_no_ui.png')
    cv2.imwrite(rgb_filtered_frame_no_ui_path, rgb_frame_without_bg)

    rgb_filtered_frame_dist_path = os.path.join(path, 'rgb_filtered_frame_dist.png')
    cv2.imwrite(rgb_filtered_frame_dist_path, rgb_frame_with_distance)

    rgb_filtered_frame_ui_path = os.path.join(path, 'rgb_filtered_frame_ui.png')
    cv2.imwrite(rgb_filtered_frame_ui_path, rgb_frame_ui)
    
    depth_frame_path = os.path.join(path, 'depth_frame.txt')
    np.savetxt(depth_frame_path, depth_frame, fmt='%.6f')

    print('centroid', centroid)
    centroid_path = os.path.join(path, 'centroid.txt')
    centroids_file = open(centroid_path, 'w+')
    x, y, z = centroid
    centroids_file.write('%.6f %.6f %.6f\n' % (x, y, z * 1000)) # converte Z de m para mm
    centroids_file.close()

    print('Frames armazenados com sucesso!')

  def build_path(self) -> str:
    volunteer_name = self.parameters['patient_name']
    light_setup = self.parameters['light_setup']
    distance = self.parameters['distance']
    type = self.parameters['type']
    rep_folder = ''
    grasp = 'aberta'

    if type == 'follow_up':
      rep_folder = f'repetition_{self.reps_counter}'
      grasp = self.follow_up_grasps[self.grasp_iterator]

    base_path = os.path.join('.', 'experiments', volunteer_name, light_setup, str(distance), type, rep_folder, grasp)

    os.makedirs(base_path, exist_ok=True)

    return base_path

  def stop(self):
    # if self.pipeline:
    #   self.pipeline.stop()
    cv2.destroyAllWindows()

class ExperimentController:
  def __init__(self, volunteer_name: str, experiment_runner: ExperimentRunner):
    default_iterations = [
      { 'type': 'gold_standard', 'repetitions': 1, 'hand_side': 'esquerda' },
      { 'type': 'follow_up', 'repetitions': 10, 'hand_side': 'direita' }
    ]

    default_distance_setups = [
      { 'distance': 28, 'iterations': default_iterations },
      { 'distance': 35, 'iterations': default_iterations },
      { 'distance': 37, 'iterations': default_iterations }
    ]

    self.setups = [
      { 'light_setup': 'luz-na-mao', 'distance_setups': default_distance_setups },
      { 'light_setup': 'luz-de-lado', 'distance_setups': default_distance_setups },
      { 'light_setup': 'luz-na-cam', 'distance_setups': default_distance_setups },
    ]

    self.volunteer_name = volunteer_name
    self.experiment_runner = experiment_runner

  def execute(self):
    try:
      self.execute_setups()
    except Exception as exception:
      print('Error executing setups: ', exception)
    # finally:
      # self.experiment_runner.stop()

  def execute_setups(self):
    for setup in self.setups:
      light_setup = setup['light_setup']
      print(f'Iniciando setup de luz: "{light_setup}"')
      distance_setups = setup['distance_setups']

      for distance_setup in distance_setups:
        distance = distance_setup['distance']
        print(f'Iniciando setup de distância: "{distance}"')
        iterations = distance_setup['iterations']

        for iteration in iterations:
          type = iteration['type']
          repetitions = iteration['repetitions']
          hand_side = iteration['hand_side']

          self.experiment_runner.set_params(
            patient_name=self.volunteer_name,
            light_setup=light_setup,
            distance=distance,
            type=type,
            repetitions=repetitions,
            hand_side=hand_side
          )

          print('Chamando "start" no experiment_runner')
          force_exit = self.experiment_runner.start()

          if force_exit:
            print('*WARN* Aplicação encerrando devido a "force_exit"')
            return

if __name__ == '__main__':
  argument_parser = ArgumentParser()
  argument_parser.add_argument('volunteer_name', help='Nome do voluntário')
  arguments = argument_parser.parse_args()
  print('Parâmetros: ', arguments)

  experiment_runner = ExperimentRunner()
  experiment_controller = ExperimentController(
    arguments.volunteer_name,
    experiment_runner
  )

  try:
    print('*** Iniciando aplicação ***')
    experiment_controller.execute()
  except Exception as exception:
    print('Erro não capturado: ', exception)

  print('*** Aplicação encerrada com sucesso! ***')
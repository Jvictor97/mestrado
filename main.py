import numpy as np
import math
import cv2
import os
from datetime import datetime
from pathlib import Path
import requests
from argparse import ArgumentParser
from metric_calculator import MetricCalculator
from dotenv import load_dotenv

load_dotenv()

def runExerciseRecorder(fromCLI=False, parameters={}, handleClose=lambda : None):
  import pyrealsense2 as rs

  is_gold_standard = None
  email = None
  password = None
  exercise = None
  is_left_hand = None


  if fromCLI:
  # arg parsing
    argument_parser = ArgumentParser()

    argument_parser.add_argument('exercise', help='nome do exercício que será realizado')
    argument_parser.add_argument('hand_side', help='Mão que será utilizada na captura (esquerda/direita)')
    argument_parser.add_argument('patient_email', help='email do paciente usado para login no sistema web')
    argument_parser.add_argument('patient_password', help='senha do paciente usado para login no sistema web')
    argument_parser.add_argument('-g', '--gold-standard', 
      action='store_true', 
      default=False,
      help='cria uma nova base padrão-ouro do exercício'
    )

    arguments = argument_parser.parse_args()
    print('reading from arguments', arguments)

    # reading arguments
    is_gold_standard = arguments.gold_standard
    email = arguments.patient_email
    password = arguments.patient_password
    exercise = arguments.exercise
    is_left_hand = arguments.hand_side == 'esquerda'
  else:
    print('reading from parameters', parameters)
    # reading parameters
    is_gold_standard = parameters['gold_standard']
    email = parameters['patient_email']
    password = parameters['patient_password']
    exercise = parameters['exercise']
    is_left_hand = parameters['hand_side'] == 'left'
  

  # realsense
  def config_camera():
    pipeline = rs.pipeline()
    config = rs.config()

    pipeline_wrapper = rs.pipeline_wrapper(pipeline)
    pipeline_profile = config.resolve(pipeline_wrapper)
    device = pipeline_profile.get_device()
    device_product_line = str(device.get_info(rs.camera_info.product_line))

    width = 640
    height = 480
    frame_rate = 60

    config.enable_stream(rs.stream.depth, width, height, rs.format.z16, frame_rate)
    config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, frame_rate)

    profile = pipeline.start(config)

    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    print("Depth Scale is: ", depth_scale)

    # We will be removing the background of objects more than
    #  clipping_distance_in_meters meters away
    clipping_distance_in_meters = 0.4
    clipping_distance = clipping_distance_in_meters / depth_scale

    print('clipping_distance', clipping_distance)

    # Create an align object
    # rs.align allows us to perform alignment of depth frames to others frames
    # The "align_to" is the stream type to which we plan to align depth frames.
    align_to = rs.stream.color
    align = rs.align(align_to)

    return pipeline, align, clipping_distance

  def predict_joint_coordinates(frame, centroid, is_left_hand, folder):
      base_url = os.getenv('AWR_URL')

      if not base_url:
        print('Crie um arquivo .env com a variável AWR_URL!!!')

      url = f'{base_url}/calculate-joint-coordinates'

      json = {
        'frame': frame.tolist(),
        'centroid': centroid,
        'is_left_hand': is_left_hand
      }

      response = requests.post(url, json=json)
      if response.status_code != 200:
        print('Erro na chamada do AWR: ', response)
      else:
        prediction = np.array(response.json()['prediction'])

        np.savetxt(f'{folder}/prediction.txt', prediction)

        print_prediction(frame, prediction, is_left_hand)

        return prediction

  def print_prediction(frame, prediction, is_left_hand):
    joints = np.reshape(prediction, (14, 3))

    if is_left_hand:
      img = np.flip(frame, 1)
    else:
      img = frame

    img = cv2.applyColorMap(cv2.convertScaleAbs(img, alpha=0.03), cv2.COLORMAP_JET)

    for joint in joints:
      x, y, z = joint
      center_x = math.ceil(x)
      center_y = math.ceil(y)
      img = cv2.circle(img, center=(center_x, center_y), radius=4, color=(0, 0, 255), thickness=-1)

    window = f'frame.txt'
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window, 640, 480)
    cv2.imshow(window, img)

  def calculate_metric(exercise, comparison_joints):
    gold_std_path = f'./images/real_time/gold_standard/{exercise}/prediction.txt'
    gold_standard_joints = np.loadtxt(gold_std_path)

    metric_calculator = MetricCalculator()
    result = metric_calculator.calculate_metric_from_joints(gold_standard_joints, comparison_joints, 14)

    print('O resultado é:', result)

    return result

  def send_metric_to_web(metric, email, password):
    # auth
    base_url = 'http://localhost:3333'

    auth_url = f'{base_url}/auth/signin'

    patient_auth = {
      'email': email, # 'jvictor.942@gmail.com',
      'password': password, # 'a'
    }

    auth_response = requests.post(auth_url, patient_auth)
    json = auth_response.json()

    token = json['token']
    userId = json['userId']

    print('response: ', json)
    print('token: ', token)

    # save metric
    save_followup_url = f'{base_url}/follow-up/save/{userId}'

    headers = {
      'Authorization': f'Bearer {token}'
    }

    current_date = datetime.today().strftime('%Y-%m-%dT%H:%M:%SZ')

    data = {
      'exercise': exercise,
      'date': current_date,
      'metric': math.ceil(metric)
    }

    save_response = requests.post(save_followup_url, data=data, headers=headers)

    print('save_response status', save_response.status_code)
    print('save_response body', save_response.json())

  def save_depth_frame(depth_frame, centroid, is_gold_standard, exercise):
    dataset_folder = 'gold_standard' if is_gold_standard else 'follow_up'
    folder = f'./images/real_time/{dataset_folder}/{exercise}'

    if not is_gold_standard:
      current_date = datetime.today().strftime('%Y-%m-%dT%H.%M.%S')
      folder += f'/{current_date}'

    Path(f'{folder}/input/').mkdir(parents=True, exist_ok=True)
    centroids_file = open(f'{folder}/input/centroid.txt', 'w+')

    print('centroid', centroid)
    file_name = f'{folder}/input/frame.txt'

    centroids_file.write('%.6f %.6f %.6f\n' % (centroid[0], centroid[1], centroid[2]))
    centroids_file.close()

    np.savetxt(file_name, depth_frame, fmt='%.6f')

    return folder

  pipeline, align, clipping_distance = config_camera()
  try:
    while True:
      # Get frameset of color and depth
      frames = pipeline.wait_for_frames()

      # Align the depth frame to color frame
      aligned_frames = align.process(frames)

      # Get aligned frames
      # aligned_depth_frame is a 640x480 depth image
      aligned_depth_frame = aligned_frames.get_depth_frame()
      color_frame = aligned_frames.get_color_frame()

      distance = aligned_depth_frame.get_distance(320, 240)
      print('distance in cm: %.2f\r' % distance * 100, end='\r')

      frames_are_valid = aligned_depth_frame and color_frame
      if not frames_are_valid:
          continue

      # FILTERS
      spatial = rs.spatial_filter()
      spatial.set_option(rs.option.filter_magnitude, 5)
      spatial.set_option(rs.option.filter_smooth_alpha, 1)
      spatial.set_option(rs.option.filter_smooth_delta, 50)
      filtered_depth = spatial.process(aligned_depth_frame)

      hole_filling = rs.hole_filling_filter()
      filled_depth = hole_filling.process(filtered_depth)

      # depth_image = np.asanyarray(aligned_depth_frame.get_data())
      depth_image = np.asanyarray(filled_depth.get_data())
      color_image = np.asanyarray(color_frame.get_data())

      background_color = 0  # black
      # depth image is 1 channel, color is 3 channels
      depth_image_3d = np.dstack((depth_image, depth_image, depth_image))
      bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), background_color, color_image)

      mass_y, mass_x = np.where((depth_image > 0) & (depth_image < clipping_distance))

      if (len(mass_x) and len(mass_y)):
        center_x = math.ceil(np.average(mass_x))
        center_y = math.ceil(np.average(mass_y))
        center_z = aligned_depth_frame.get_distance(center_x, center_y)
        bg_removed = cv2.circle(bg_removed, center=(center_x, center_y), radius=2, color=(0, 0, 255), thickness=-1)

      # Render images:
      #   depth align to color on left
      #   depth on right
      # cv2.convertScaleAbs(depth_image_3d, alpha=0.03) #
      depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
      images = np.hstack((bg_removed, depth_colormap))

      cv2.namedWindow('exercise-recorder', cv2.WINDOW_NORMAL)
      cv2.resizeWindow('exercise-recorder', 1280, 480)
      cv2.imshow('exercise-recorder', images)

      key = cv2.waitKey(1)

      keys = {
        'ENTER': 13,
        'ESC': 27
      }

      if key == keys['ENTER']:
        # captura frame para comparação
        depth_frame = depth_image.copy()
        centroid = [center_x, center_y, center_z * 1000]
    
        folder_saved = save_depth_frame(depth_frame, centroid, is_gold_standard, exercise)
        comparison_joints = predict_joint_coordinates(depth_frame, centroid, is_left_hand, folder_saved)

        if not is_gold_standard:
          metric = calculate_metric(exercise, comparison_joints)
          send_metric_to_web(metric, email, password)
      elif key == keys['ESC']:
        cv2.destroyAllWindows()
        handleClose()
        break
  except Exception as e:
    print('Error during processing:', e)
  finally:
    pipeline.stop()


if __name__ == '__main__':
  runExerciseRecorder(fromCLI=True)
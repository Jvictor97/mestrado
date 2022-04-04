import pyrealsense2 as rs
import numpy as np
import math
import cv2
from datetime import datetime
from pathlib import Path
import requests

pipeline = rs.pipeline()
config = rs.config()

pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

width = 640
height = 480
frame_rate = 30

config.enable_stream(rs.stream.depth, width, height, rs.format.z16, frame_rate)
config.enable_stream(rs.stream.color, width, height,
                     rs.format.bgr8, frame_rate)

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

frame_count = 0
current_date = datetime.today().strftime('%Y-%m-%d')
dataset_root = f'./images/dataset/{current_date}-2/'
Path(dataset_root).mkdir(parents=True, exist_ok=True)
centroids_file = open(f'{dataset_root}/centroids.txt', 'w+')


def predict_joint_coordinates(frame, centroid):
    base_url = 'http://c92f-35-221-42-15.ngrok.io'
    url = f'{base_url}/calculate-joint-coordinates'

    json = {
        'frame': frame.tolist(),
        'centroid': centroid
    }

    response = requests.post(url, json=json)
    if response.status_code != 200:
        print('Deu ruim!')
    else:
        prediction = np.array(response.json()['prediction'])

        joints = np.reshape(prediction, (14, 3))
        img = np.flip(frame, 1)

        img = cv2.applyColorMap(cv2.convertScaleAbs(
            img, alpha=0.03), cv2.COLORMAP_JET)

        for joint in joints:
            x, y, z = joint
            center_x = math.ceil(x)
            center_y = math.ceil(y)
            img = cv2.circle(img, center=(center_x, center_y),
                             radius=2, color=(0, 0, 255), thickness=-1)

        window = f'frame.txt'
        cv2.namedWindow(window, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window, 640, 480)
        cv2.imshow(window, img)
        # cv2.waitKey(2000)
        # cv2.destroyWindow(window)


def capture_depth_frame(depth_frame, centroid):
    global frame_count, centroids_file
    print('centroid', centroid)
    file_name = f'{dataset_root}/frame_{frame_count}.txt'
    centroids_file.write('%.6f %.6f %.6f\n' %
                         (centroid[0], centroid[1], centroid[2]))
    centroids_file.flush()
    np.savetxt(file_name, depth_frame, fmt='%.6f')
    frame_count += 1

    predict_joint_coordinates(depth_frame, centroid)


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
        bg_removed = np.where((depth_image_3d > clipping_distance) | (
            depth_image_3d <= 0), background_color, color_image)

        mass_y, mass_x = np.where((depth_image > 0) & (
            depth_image < clipping_distance))

        if (len(mass_x) and len(mass_y)):
            center_x = math.ceil(np.average(mass_x))
            center_y = math.ceil(np.average(mass_y))
            center_z = aligned_depth_frame.get_distance(center_x, center_y)
            bg_removed = cv2.circle(bg_removed, center=(
                center_x, center_y), radius=2, color=(0, 0, 255), thickness=-1)

        # Render images:
        #   depth align to color on left
        #   depth on right
        # cv2.convertScaleAbs(depth_image_3d, alpha=0.03) #
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(
            depth_image, alpha=0.03), cv2.COLORMAP_JET)
        images = np.hstack((bg_removed, depth_colormap))

        cv2.namedWindow('exercise-recorder', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('exercise-recorder', 1280, 480)
        cv2.imshow('exercise-recorder', images)

        key = cv2.waitKey(1)

        keys = {
            'ENTER': 13,
            'SPACE': 32,
            'ESC': 27
        }

        if key == keys['SPACE']:
          # captura frame de referência
            print('ESPAÇOOOOO')
        if key == keys['ENTER']:
          # captura frame para comparação
            capture_depth_frame(depth_image.copy(), [
                                center_x, center_y, center_z * 1000])
        elif key == keys['ESC']:
            cv2.destroyAllWindows()
            break
finally:
    centroids_file.close()
    pipeline.stop()

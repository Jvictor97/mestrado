import pyrealsense2 as rs
import numpy as np
import math
import cv2
import os, psutil

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
config.enable_stream(rs.stream.color, width, height, rs.format.bgr8, frame_rate)

profile = pipeline.start(config)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)

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

frames_to_save = list()

def capture_depth_frames(depth_frame):
    frames_to_save.append(depth_frame)
    print('frames', len(frames_to_save))
    process = psutil.Process(os.getpid())
    print('Memória em MB:', process.memory_info().rss / 1024 ** 2) 

try:
    while True:
        # Get frameset of color and depth
        frames = pipeline.wait_for_frames()

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame() # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        frames_are_valid = aligned_depth_frame and color_frame
        if not frames_are_valid:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        background_color = 0 # black
        depth_image_3d = np.dstack((depth_image,depth_image,depth_image)) #depth image is 1 channel, color is 3 channels
        bg_removed = np.where((depth_image_3d > clipping_distance) | (depth_image_3d <= 0), background_color, color_image)

        mass_x, mass_y = np.where((depth_image > 0) & (depth_image < clipping_distance))

        if (len(mass_x) and len(mass_y)):
            center_x = np.average(mass_x)
            center_y = np.average(mass_y)
            bg_removed = cv2.circle(bg_removed, center=(math.ceil(center_y), math.ceil(center_x)), radius=2, color=(0, 0, 255), thickness=-1)

        # Render images:
        #   depth align to color on left
        #   depth on right
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET) # cv2.convertScaleAbs(depth_image_3d, alpha=0.03) #        
        images = np.hstack((bg_removed, depth_colormap))
        
        cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Align Example', 1280, 480)
        cv2.imshow('Align Example', images)
        
        key = cv2.waitKey(1)

        if key == 13:
            capture_depth_frames(depth_image.copy())
        elif key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()



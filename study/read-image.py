# import cv2
# import numpy as np
# import matplotlib.pyplot as plt

# hand_centers_file = open('./images/nyu/center_test_refined.txt', 'r')
# hand_centers = hand_centers_file.read()

# # lines = hand_centers.split('\n')
# # x,y,z = lines[0].split()
# # print('x', x, 'y', y, 'z', z)

# # img = cv2.imread('./images/nyu/depth_1_0000001.png', 0) 
# img = cv2.imread('./images/nyu/cat.jpg', 0) 
# # cv2.imshow('image', img)
# # cv2.waitKey(0)
# # cv2.destroyAllWindows()

# plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

# # plt.imshow(img, interpolation = 'bicubic')
# plt.show()

import cv2
import matplotlib.pyplot as plt

image = cv2.imread("./images/nyu/depth_1_0000001.png")
plt.axis("off")
plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
plt.show()
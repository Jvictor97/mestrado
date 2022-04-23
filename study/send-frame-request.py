# import requests
# import numpy as np

# url = 'http://localhost:5000/calculate-joint-coordinates'
# frame = np.loadtxt('../images/dataset/2022-03-23-2/frame_0.txt')

# body = { 'frame': frame.tolist() }
# response = requests.post(url, json=body)

# print(response.status_code)
# print(response.text)

import requests
import numpy as np

url = 'http://localhost:5000/upload'
frame = open('../images/dataset/2022-03-23-2/frame_0.txt')

files = { 'frame': frame }
response = requests.post(url, files=files)

print(response.status_code)
print(response.text)
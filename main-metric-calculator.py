import requests
from metric_calculator import MetricCalculator
from datetime import datetime
import math

root = './images/real_time'
g_std = f'{root}/gold_standard'
f_up = f'{root}/follow_up'
exercise = 'extension'

metric_calculator = MetricCalculator(g_std, f_up)

result = metric_calculator.calculate_metrics(exercise, '2022-04-10', 14)
print('O resultado é:', result)

# auth
base_url = 'http://localhost:3333'

auth_url = f'{base_url}/auth/signin'

patient_auth = {
  'email': 'jvictor.942@gmail.com',
  'password': 'a'
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

current_date = datetime.today().strftime('%Y-%m-%d')

data = {
  'exercise': exercise,
  'date': current_date,
  'metric': math.ceil(result)
}

save_response = requests.post(save_followup_url, data=data, headers=headers)

print('save_response status', save_response.status_code)
print('save_response body', save_response.json())

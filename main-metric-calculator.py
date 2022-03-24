from metric_calculator import MetricCalculator

root = './results'
g_std = f'{root}/gold_standard'
f_up = f'{root}/follow_up'

metric_calculator = MetricCalculator(g_std, f_up)

result = metric_calculator.calculate_metrics('extension', '2022-03-21', 14)

print('O resultado é:', result)
with open('pipeline_p3_player_metrics.py', 'r') as f:
    text = f.read()
import re
col_accesses = set(re.findall(r'\[["\']([a-zA-Z0-9_]+)["\']\]', text))
print('Columns accessed in pipeline_p3:')
print(sorted(list(col_accesses)))


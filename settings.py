import os

LOCK_KEY = 'metrics_lock'
LOCKFILES_DIR = os.path.dirname(__name__)
METRICS_FILE =  os.path.join(os.path.dirname(__name__), 'metrics.json')


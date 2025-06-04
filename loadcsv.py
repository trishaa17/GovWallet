# import time
# import requests
# import pandas as pd
# from io import StringIO

# _csv_cache = {'data': None, 'last_updated': 0}
# TTL_SECONDS = 300  # refresh every 5 minutes

# def load_csv_data():
#     now = time.time()
#     if _csv_cache['data'] is None or (now - _csv_cache['last_updated']) > TTL_SECONDS:
#         url = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"
#         response = requests.get(url)
#         response.raise_for_status()
#         csv_data = response.content.decode('utf-8')
#         df = pd.read_csv(StringIO(csv_data))
#         _csv_cache['data'] = df
#         _csv_cache['last_updated'] = now  # <- missing!
#     return _csv_cache['data'].copy()

import time
import requests
import pandas as pd
from io import StringIO

_csv_cache = {'data': None, 'last_updated': 0}
TTL_SECONDS = 300  # 5 minutes

DATA_URL = "https://wacsg2025-my.sharepoint.com/:x:/p/trisha_teo/EfFwqNRlqjdKgUnvBWe53SEBKKJA9yK7RomjADmwfuT6iQ?download=1"

def load_csv_data():
    now = time.time()
    if _csv_cache['data'] is None or (now - _csv_cache['last_updated']) > TTL_SECONDS:
        print("Fetching CSV data from source...")
        response = requests.get(DATA_URL)
        response.raise_for_status()
        csv_data = response.content.decode('utf-8')
        df = pd.read_csv(StringIO(csv_data))
        _csv_cache['data'] = df
        _csv_cache['last_updated'] = now
    return _csv_cache['data'].copy()

def force_refresh():
    print("Force refreshing CSV cache...")
    response = requests.get(DATA_URL)
    response.raise_for_status()
    csv_data = response.content.decode('utf-8')
    df = pd.read_csv(StringIO(csv_data))
    _csv_cache['data'] = df
    _csv_cache['last_updated'] = time.time()

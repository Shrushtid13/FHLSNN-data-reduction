import time
import os
import sys

# disable network for this script to prove cache
import urllib.request
def guard(*args, **kwargs):
    raise Exception("Network is disabled")
urllib.request.urlopen = guard

from sklearn.datasets import fetch_openml

print("Loading Pendigits...")
t0 = time.time()
pendigits = fetch_openml('pendigits', version=1, parser='auto')
print(f"Loaded Pendigits in {time.time() - t0:.2f}s, shape {pendigits.data.shape}")

print("Loading Letter...")
t0 = time.time()
letter = fetch_openml('letter', version=1, parser='auto')
print(f"Loaded Letter in {time.time() - t0:.2f}s, shape {letter.data.shape}")

# Find openml cache folder
home = os.path.expanduser('~')
cache_dir = os.path.join(home, 'scikit_learn_data', 'openml')
print(f"Cache dir: {cache_dir}")

for root, dirs, files in os.walk(cache_dir):
    for name in files:
        print(" ", os.path.join(root, name))

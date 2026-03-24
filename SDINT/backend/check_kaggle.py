import os
import sys
import kagglehub
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

path = kagglehub.dataset_download("pavellexyr/the-reddit-dataset-dataset")
print("Path to dataset files:", path)

for f in os.listdir(path):
    print(f"File: {f}, Size: {os.path.getsize(os.path.join(path, f)) / (1024*1024):.2f} MB")

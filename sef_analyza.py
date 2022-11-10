import os
import pandas as pd
from paths import *


files = []

for file in os.scandir(PROLINE_RAW_DATA_PATH):
    if file.is_file():
        files.append(file)


df = pd.read_excel(files[0])
# print(df)

spectral_count = df.iloc[:, :15].dropna().set_index('Description')
spectral_count['tmp'] = spectral_count['K1'].apply(lambda row: row + 1)
print(spectral_count)

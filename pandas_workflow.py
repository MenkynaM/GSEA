import os

import numpy as np
import pandas as pd

from paths import PROLINE_RAW_DATA_PATH

files = []

for file in os.scandir(PROLINE_RAW_DATA_PATH):
    if file.is_file():
        files.append(file)


df = pd.read_excel(files[0], sheet_name='CD8')
df = df.dropna()
df['Description'] = df.loc[:, 'Description'].apply(lambda x: x[:x.find('OS') - 1])
df = df.iloc[:, :16].set_index('Description')

# print(df.columns)

col_all = [col for col in df.columns if 'K' in col or 'Z' in col]
col_zdravi = [col for col in col_all if 'Z' in col]
col_karcinom = [col for col in col_all if 'K' in col]

df['zdr_mean'] = df.loc[:, col_zdravi].mean(axis=1)
df['karcinom_mean'] = df.loc[:, col_karcinom].mean(axis=1)


for col in col_all:

    def tfun(x):
        mean_col = 'karcinom_mean'
        if col in col_karcinom:
            mean_col = 'zdr_mean'
        return np.log2(x[col] / x[mean_col]) if (x[mean_col] != 0) and (x[col] != 0) else 0


    df[col + '_fc'] = df.apply(tfun, axis=1)


fc_col_all = [col for col in df.columns if '_fc' in col]
fc_col_zdravi = [col for col in fc_col_all if 'Z' in col]
fc_col_karcinom = [col for col in fc_col_all if 'K' in col]



print(df.loc[1, df.loc[1, col_karcinom > 0]])
# [print(col) for col in df.columns]
# print(col_zdravi)


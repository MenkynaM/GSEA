import os

# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from paths import *

# plt.rcParams.update({
#     "text.usetex": True
# })

files = []

for file in os.scandir(PROLINE_RAW_DATA_PATH):
    if file.is_file():
        files.append(file)


df = pd.read_excel(files[0])
# print(df)


def calc_fc(x, series: pd.Series):
    return x - series.mean()

# fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
# fig.suptitle('Pocet proteinov')
# x = np.arange(1, 8.1, 1)
# y1 = np.array([15, 8, 3, 8, 11, 10, 6, np.nan])
# y2 = np.array([18, 19, 46, 22, 15, 30, 46, 61])
# ax1.plot(x, y1, 'ro--')
# ax1.set_xlabel('Karcinom')
# ax2.plot(x, y2, 'g^--')
# ax2.set_xlabel('Zdrave pacientky')
# plt.show()
# plt.plot(x, y1, 'ro--', x, y2, 'g^--')
# plt.show()


spectral_count = df.iloc[:, :16].dropna().set_index('Description')
col_zdravi = [col for col in spectral_count.columns if 'Z' in col]
col_karcinom = [col for col in spectral_count.columns if 'K' in col]

inp = input().split(' ')

sets = {c: set(spectral_count.loc[spectral_count[c] > 0, [c]].index) for c in col_karcinom}
vybrane = [sets[elem] for elem in col_karcinom if elem in inp]
zvysne = [sets[elem] for elem in col_karcinom if elem not in inp]
inter = set(spectral_count.index).intersection(*vybrane)
print(len(inter.difference(*zvysne)))


# sets = {c: set(spectral_count.loc[spectral_count[c] > 0, [c]].index) for c in col_karcinom}
# vybrane = [sets[elem] for elem in col_karcinom if elem in inp]
# zvysne = [sets[elem] for elem in col_karcinom if elem not in inp]
# inter = set(spectral_count.index).intersection(*vybrane)
# print(len(inter.difference(*zvysne)))





# for col in spectral_count.columns:
#     if col in col_karcinom:
# print(spectral_count[col])
# spectral_count[col + '-logFC'] = spectral_count[col].apply(calc_fc, args=())
# for col in cols:
#     if col[0] == 'K':
# idx_start, idx_end =
#     spectral_count[col + '-FC'] =
# print(col)
# spectral_count['tmp'] = spectral_count['K1'].apply(lambda row: row + 1)
# print(cols)

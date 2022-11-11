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

# comb = {k: v for k in col_zdravi for v in col_karcinom}
# comb = [(zdr, kar) for zdr in col_karcinom for kar in col_karcinom if zdr != kar]
# d = {}


inp = input().split(' ')
sets = {c: set(spectral_count.loc[spectral_count[c] > 0, [
               c]].index) for c in col_karcinom}
vybrane = [sets[elem] for elem in col_karcinom if elem in inp]
zvysne = [sets[elem] for elem in col_karcinom if elem not in inp]
# prvy = vybrane[0]
# print(len(set(prvy).intersection(*vybrane)))
inter = set(spectral_count.index).intersection(*vybrane)
# print(zvysne)
print(len(inter.difference(*zvysne)))

# print(len())

# tmp = sets[0].intersection(sets[1])
# for s in sets:
#     tmp = tmp.intersection(s)
# for z in zvysok:
#     tmp = tmp.difference(set(spectral_count[z].index))
# print(len(tmp))

# for c in comb:
#     s1 = set(spectral_count.loc[spectral_count[c[0]] > 0, [c[0]]].index)
#     s2 = set(spectral_count.loc[spectral_count[c[1]] > 0, [c[1]]].index)
#     d[c] = len(s1.intersection(s2))


# for key, val in d.items():
#     print(str(key) + ' - ' + str(val))

# print(len(d))
# print(set(spectral_count.loc[spectral_count[comb[0][0]] > 0, [comb[0][0]]].index))
# for zdr in col_zdravi:
#     for kar in col_karcinom:
#         print(zdr, kar)

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

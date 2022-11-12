import os

# import matplotlib.pyplot as plt
# import numpy as np
import pandas as pd

from paths import PROLINE_RAW_DATA_PATH

# plt.rcParams.update({
#     "text.usetex": True
# })

files = []

for file in os.scandir(PROLINE_RAW_DATA_PATH):
    if file.is_file():
        files.append(file)


df = pd.read_excel(files[0], sheet_name='CD8')
# print(df)

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
col_all = [col for col in spectral_count.columns if 'K' in col or 'Z' in col]

col_vybrany = col_zdravi

inp = input().split(' ')

while not inp == ['q']:
    if col_vybrany != col_all:
        inp = ['K' + i if col_vybrany == col_karcinom else 'Z' + i for i in inp]
    sets = {c: set(spectral_count.loc[spectral_count[c] > 0, [c]].index) for c in col_vybrany}
    vybrane = [sets[elem] for elem in col_vybrany if elem in inp]
    zvysne = [sets[elem] for elem in col_vybrany if elem not in inp]

    inter = set(spectral_count.index).intersection(*vybrane)
    # print(inp)
    vysledok = len(inter.difference(*zvysne))
    print(f'{vysledok} \t farba ma byt {2 * vysledok}')
    inp = input().split(' ')



import os
import pandas as pd
from gsea_new import get_sample_code

orig_path = os.getcwd()
os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\HER2-_Ki67_nad_14\HER2-_Ki67_nad_14")

LUMA_CD4 = pd.read_csv('CD4.csv', index_col=0).drop(columns=['Description'])
LUMA_CD4 = LUMA_CD4.drop(
    columns=[val for val in LUMA_CD4.columns if 'Z' in val])
LUMA_CD4.columns = ['LUMA' + str(i + 1) for i in range(5)]

os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\HER2-_Ki67_pod_14\HER2-_Ki67_pod_14")
LUMB_CD4 = pd.read_csv('CD4.csv', index_col=0).drop(columns=['Description'])
LUMB_CD4 = LUMB_CD4.drop(
    columns=[val for val in LUMB_CD4.columns if 'Z' in val])
# LUMB_CD4.columns = [name.split(' ')[-1] for name in LUMB_CD4.columns]
LUMB_CD4.columns = ['LUMB' + str(i + 1) for i in range(5)]

os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\TNBC\TNBC")
TNBC_CD4 = pd.read_csv('CD4.csv', index_col=0).drop(columns=['Description'])
TNBC_CD4.columns = [
    'TNBC' + str(i + 1) if i < 5 else 'ZDRAVI' + str(i - 4) for i in range(15)]

print(LUMA_CD4, LUMB_CD4, TNBC_CD4)


os.chdir(orig_path)
# merge = pd.concat([LUMA_CD4, LUMB_CD4, TNBC_CD4], axis=1)
merge = LUMA_CD4.join(LUMB_CD4).join(TNBC_CD4)
phenotypes = pd.DataFrame({col: get_sample_code(
    col)[0] for col in merge.columns}, index=['phenotype'])
merge = pd.concat([phenotypes, merge])
merge[merge == 0] = 'NA'
merge[merge == ''] = 'NA'
# merge.fillna('NA')

merge.to_csv('merge.csv', index=True)

with open('merge.csv', 'r') as file:
    text = ','.join([s if s != '' else 'NA' for s in file.read().split(',')])
with open('merge2.csv', 'w') as f:
    f.write(text)
# print(merge)


orig_path = os.getcwd()
os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\HER2-_Ki67_nad_14\HER2-_Ki67_nad_14")

LUMA_CD4 = pd.read_csv('updownCD4.csv', index_col=0).drop(
    columns=['Description'])
# LUMA_CD4 = LUMA_CD4[LUMA_CD4['(abs(log Ratio) >= 1) and (bbinomial PValue <= 0.05)']].drop(columns=['bbinomial PValue', '-log10(bbinomial PValue)', 'log Ratio', '(abs(log Ratio) >= 1) and (bbinomial PValue <= 0.05)'])
LUMA_CD4 = LUMA_CD4.loc[(abs(LUMA_CD4['log Ratio']) > 1.5) & (LUMA_CD4['bbinomial PValue'] < 0.05)].drop(columns=[
    'bbinomial PValue', '-log10(bbinomial PValue)', 'log Ratio', '(abs(log Ratio) >= 1) and (bbinomial PValue <= 0.05)'])
LUMA_CD4 = LUMA_CD4.drop(
    columns=[val for val in LUMA_CD4.columns if 'Z' in val])
LUMA_CD4.columns = ['LUMA' + str(i + 1) for i in range(5)]

os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\HER2-_Ki67_pod_14\HER2-_Ki67_pod_14")
LUMB_CD4 = pd.read_csv('updownCD4.csv', index_col=0).drop(
    columns=['Description'])
LUMB_CD4 = LUMB_CD4.loc[(abs(LUMB_CD4['log Ratio']) > 1.5) & (LUMB_CD4['bbinomial PValue'] < 0.05)].drop(columns=[
    'bbinomial PValue', '-log10(bbinomial PValue)', 'log Ratio', '(abs(log Ratio) >= 1) and (bbinomial PValue <= 0.05)'])
LUMB_CD4 = LUMB_CD4.drop(
    columns=[val for val in LUMB_CD4.columns if 'Z' in val])
LUMB_CD4.columns = ['LUMB' + str(i + 1) for i in range(5)]

os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\TNBC\TNBC")
TNBC_CD4 = pd.read_csv('updownCD4.csv', index_col=0).drop(
    columns=['Description'])
TNBC_CD4 = TNBC_CD4.loc[(abs(TNBC_CD4['log Ratio']) > 1.5) & (TNBC_CD4['bbinomial PValue'] < 0.05)].drop(columns=[
    'bbinomial PValue', '-log10(bbinomial PValue)', 'log Ratio', '(abs(log Ratio) >= 1) and (bbinomial PValue <= 0.05)'])
TNBC_CD4.columns = [
    'TNBC' + str(i + 1) if i < 5 else 'ZDRAVI' + str(i - 4) for i in range(15)]

print(LUMA_CD4)
print(LUMB_CD4)
print(TNBC_CD4)


os.chdir(orig_path)
# merge = LUMA_CD4.join(LUMB_CD4).join(TNBC_CD4)
merge1 = pd.concat([LUMA_CD4, LUMB_CD4, TNBC_CD4], axis=1)
phenotypes1 = pd.DataFrame({col: get_sample_code(
    col)[0] for col in merge.columns}, index=['phenotype'])
merge1 = pd.concat([phenotypes1, merge1])
merge1[merge1 == 0] = 'NA'
# merge[merge == ''] = 'NA'
merge1.fillna(0)

merge1.to_csv('merge3.csv', index=True)

with open('merge3.csv', 'r') as file:
    text = ','.join([s if s != '' else 'NA' for s in file.read().split(',')])
with open('merge4.csv', 'w') as f:
    f.write(text)
print(merge1)

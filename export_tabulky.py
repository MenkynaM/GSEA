import pandas as pd
from bs4 import BeautifulSoup
from paths import GSEA_OUTPUT_PATH, select_dir
import os


# os.chdir(GSEA_OUTPUT_PATH)
# print(os.getcwd())

# dirs = [direc for direc in os.scandir() if direc.is_dir()]
# print(dirs)
# os.chdir(select_dir(GSEA_OUTPUT_PATH))
# print(os.getcwd())


df = pd.read_excel(r'C:\Users\Menkyna\Documents\DATA_vyskum\Glyco_MYC_Hypo.xlsx', sheet_name='Hypo', header=0)
df_zdravi = df.loc[:, ['prot_zdr', 'SCORE_zdr']].dropna().rename(columns={'prot_zdr': 'prot'})
df_LUMA = df.loc[:, ['prot_LUMA', 'SCORE_LUMA']].dropna().rename(columns={'prot_LUMA': 'prot'})
df_LUMB = df.loc[:, ['prot_LUMB', 'SCORE_LUMB']].dropna().rename(columns={'prot_LUMB': 'prot'})
df_TNBC = df.loc[:, ['prot_TNBC', 'SCORE_TNBC']].dropna().rename(columns={'prot_TNBC': 'prot'})
# print(df_zdravi, df_LUMA)
df_mix = df_zdravi.merge(df_LUMA, how='outer', on='prot').merge(df_LUMB, how='outer', on='prot').merge(df_TNBC, how='outer', on='prot')
df_mix.fillna('NaN', inplace=True)
df_mix.to_csv('Hypo.csv', index=False)

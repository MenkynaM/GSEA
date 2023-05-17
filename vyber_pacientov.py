import os, pandas as pd, id_mapping
from random import choice
from paths import *
import tkinter as tk
from tkinter import filedialog
# from bs4 import BeautifulSoup


def get_all_patients():
    os.chdir(RAW_DATA_PATH)
    files = [f.name for f in os.scandir() if f.is_file()]
    print(files)

    df_p0vsZ = pd.read_csv(files[0])
    df_p0vsp1 = pd.read_csv(files[1])
    df_p0vsp1.columns = [col.split(' ')[-1] if 'Weighted' in col else col for col in df_p0vsp1.columns]
    df_p0vsp1.set_index('Protein Set', inplace=True)
    df_p0vsZ.columns = [col.split(' ')[-1] if 'Weighted' in col else col for col in df_p0vsZ.columns]
    df_p0vsZ.set_index('Protein Set', inplace=True)
    df_p0vsp1.rename(index=id_mapping.get_prot_description(list(df_p0vsp1.index)), inplace=True)
    df_p0vsZ.rename(index=id_mapping.get_prot_description(list(df_p0vsZ.index)), inplace=True)
    cols_to_use = df_p0vsZ.columns.difference(df_p0vsp1.columns)
    df = pd.merge(df_p0vsZ[cols_to_use], df_p0vsp1, how='outer', on='Protein Set').fillna(0)
    df.columns = [col[:1] + '0' + col[1:] if len(col) == 2 else col for col in df.columns]
    df.columns = [col.split('_')[0][:1] + '0' + col.split('_')[0][-1] + '_2' if len(col.split('_')[0]) == 2 else col for col in df.columns]
    df.columns = ['y' + col if '_2' in col else 'x' + col for col in df.columns]
    df.sort_index(axis=1, inplace=True)
    df.columns = [col[1:] for col in df.columns]
    return df






def get_pathway_list(path: os.PathLike | str) -> tuple:
    pathway_lists = [file.name for file in os.scandir(path) if 'gsea_report' in file.name and '.tsv' in file.name]
    up_pathways = list(pd.read_csv(pathway_lists[0], sep='\t')['NAME'])
    down_pathways = list(pd.read_csv(pathway_lists[1], sep='\t')['NAME'])
    return (up_pathways, down_pathways)


def main():
    root = tk.Tk()
    root.withdraw()
    dir_path = filedialog.askdirectory(initialdir=GSEA_OUTPUT_PATH)
    # print(os.path.basename(dir_path), os.path.dirname(dir_path))
    old_path = os.getcwd()
    os.chdir(dir_path)
    print(os.getcwd())
    up, down = get_pathway_list(dir_path)
    random_pathway = choice(up)
    df = pd.read_csv(random_pathway + '.tsv', sep='\t')
    print(random_pathway)
    print(df)




    os.chdir(old_path)

if __name__ == '__main__':
    main()
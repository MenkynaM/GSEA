import os, pandas as pd, id_mapping
from paths import *
import tkinter as tk
from tkinter import filedialog
# from bs4 import BeautifulSoup




def main():
    root = tk.Tk()
    root.withdraw()
    dir_path = filedialog.askdirectory(initialdir=GSEA_OUTPUT_PATH)
    # print(os.path.basename(dir_path), os.path.dirname(dir_path))
    old_path = os.getcwd()
    os.chdir(dir_path)
    pathway_lists = [file.name for file in os.scandir() if 'gsea_report' in file.name and '.tsv' in file.name]
    up_pathways = list(pd.read_csv(pathway_lists[0], sep='\t')['NAME'])
    down_pathways = list(pd.read_csv(pathway_lists[1], sep='\t')['NAME'])
    print(up_pathways, '\n', down_pathways)



    os.chdir(old_path)

if __name__ == '__main__':
    main()
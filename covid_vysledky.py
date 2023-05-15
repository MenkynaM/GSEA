import os
import paths
import id_mapping
import pandas as pd


def convert_df(df: pd.DataFrame, upregulated: bool = True) -> pd.DataFrame:
    # choice = df['log Ratio'] > 0 if upregulated else df['log Ratio'] < 0
    # df_new = df.loc[(choice)].copy()
    prot_names = list(df['Protein Set'])
    print(prot_names)
    prot_names = id_mapping.get_prot_description(prot_names)
    return df['Protein Set'].replace(prot_names, inplace=True).copy()


def obtain_results(file) -> None:
    df = pd.read_csv(file)
    df.rename(columns={'(abs(log Ratio) >= 1.5) and (bbinomial PValue <= 0.05)': 'condition'}, inplace=True)
    df.columns = [col.split(' ')[-1] if 'Weighted' in col else col for col in df.columns]
    df = df.loc[df['condition'] == True].copy()
    df.drop(columns=['-log10(bbinomial PValue)', 'condition'], inplace=True)
    prot_names = list(df['Protein Set'])
    print(prot_names)
    prot_names = id_mapping.get_prot_description(prot_names)
    print(df)
    df['Protein Set'].replace(prot_names, inplace=True)
    df_final = df.sort_values(by='log Ratio', ascending=False)
    df_final.set_index('Protein Set', inplace=True)
    df_final.to_csv(file.path[:-4] + '_conv.csv', sep=';')



if __name__ == '__main__':
    old_cd = os.getcwd()
    os.chdir(r'C:\Users\Menkyna\Documents\DATA_vyskum\vysledky_z_proline\covid\2023-05-10')
    for file in os.scandir():
        if file.is_file() and ('updown' in file.name) and ('conv' not in file.name):
            print(file.path)
            obtain_results(file)
    os.chdir(old_cd)
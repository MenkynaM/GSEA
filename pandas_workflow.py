import os

import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None


from paths import PROLINE_RAW_DATA_PATH

# print(df.columns)

# col_all = [col for col in df.columns if 'K' in col or 'Z' in col]
# col_zdravi = [col for col in col_all if 'Z' in col]
# col_karcinom = [col for col in col_all if 'K' in col]

# df['zdr_mean'] = df.loc[:, col_zdravi].mean(axis=1)
# df['karcinom_mean'] = df.loc[:, col_karcinom].mean(axis=1)


# for col in col_all:
#     def tfun(x):
#         mean_col = 'karcinom_mean'
#         if col in col_karcinom:
#             mean_col = 'zdr_mean'
#         return np.log2(x[col] / x[mean_col]) if (x[mean_col] != 0) and (x[col] != 0) else 0


#     df[col + '_fc'] = df.apply(tfun, axis=1)


# fc_col_all = [col for col in df.columns if '_fc' in col]
# fc_col_zdravi = [col for col in fc_col_all if 'Z' in col]
# fc_col_karcinom = [col for col in fc_col_all if 'K' in col]



# conditions = [df[col] > 0 for col in col_zdravi]


# print(df.loc[np.bitwise_and.reduce(conditions), fc_col_all])
# [print(col) for col in df.columns]
# print(col_zdravi)

def calculate_fc(dfs: dict[int | str: pd.DataFrame]):
    retval = {}
    for znak in dfs:
        df = dfs[znak]
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
        retval[znak] = df
    return retval


def change_format(dfs: dict[int | str: pd.DataFrame]):
    retval = {}
    for znak in dfs:
        df = dfs[znak].dropna()
        df['Description'] = df['Description'].apply(lambda x: x[:x.find('OS') - 1])
        df = df.set_index('Description')
        # df = df.loc[:, df.columns[1:]]
        retval[znak] = df
    return retval

def main():
    for file in os.scandir(PROLINE_RAW_DATA_PATH):
        if file.is_file():
            dfs = pd.read_excel(file, sheet_name=None)
            dfs = change_format(dfs)
            dfs = calculate_fc(dfs)
            print(dfs['CD19'])
    

if __name__ == '__main__':
    main()
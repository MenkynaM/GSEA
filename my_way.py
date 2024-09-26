import os


def read_data(file: str) -> dict:
    with open(file, 'r', encoding='utf8') as f:
        header = next(f)
        labels = [cell.split(' ')[-1] for cell in header.split(',')[2:-4]] + header.split(',')[-4:-1]
        value_dict = {}
        for line in f.readlines():
            protein = line.split(',')[0]
            if not '"' in line:
                values = [float(v) for v in line.split(',')[2:-1]]
            else:
                values = [float(v) for v in line.split('"')[2].split(',')[1:-1]]
            values = {labels[idx]: values[idx]  for idx in range(len(labels))}
            value_dict[protein] = values
    # with open('test.json', 'w') as f:
    #     json.dump(value_dict, f)
    return value_dict


def filter_data(data: dict, pmax: float = 0.05, abs_log_fc: float = 1.5) -> dict:
    return {k: v for k, v in data.items() if float(v['bbinomial PValue']) < pmax and abs(float(v['log Ratio'])) > abs_log_fc}


def merge_dicts(dict1: dict, dict2: dict, include_heathy=False):
    # assert len(list(dict1)[1]) == len(list(dict2)[1]), f'Dictionaries are not of the same length - len(d1) = {len(list(dict1)[1])}, len(d2) = {len(list(dict2)[1])}'
    if not include_heathy:
        for key in dict1.keys():
            dict1[key] = {k: v for k, v in dict1[key].items() if 'Z' not in k}
        for key in dict2.keys():
            dict2[key] = {k: v for k, v in dict2[key].items() if 'Z' not in k}
    print(f'{dict1} \n\n {dict2}')
    for k, v in dict1.items():
        dict1[k] = 





# orig_path = os.getcwd()
# os.chdir(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\TNBC")
files = [item for item in os.walk(r"C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\TNBC")]
# print(files)
TNBC_CD4 = filter_data(read_data(r'C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\TNBC\updownCD4.csv'), pmax=0.05, abs_log_fc=2.)
TNBC_CD8 = filter_data(read_data(r'C:\Users\Menkyna\Documents\DATA_vyskum\2023-03-10-Csilla\TNBC\updownCD8.csv'), 0.05, 2.)

merge_dicts(TNBC_CD4, TNBC_CD8)

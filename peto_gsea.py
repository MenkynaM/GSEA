import os
from paths import *


def convert(file: str) -> None:
    '''Converts a file into its corresponding .csv counterpart
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '_conv.csv'
    with open(file, 'r', encoding='utf8') as f:
        text = '"' + '","'.join([b.strip()
                                 for b in next(f).split(';')]) + '"\n'
        for line in f:
            ids, vals = line.split(';')[0], line.split(';')[1:]
            text = text + '"' + ids + '",' + ','.join(vals)
    write_file(file_name, CONVERTED_DIR_PATH, text)



def txt2csv(file: str) -> None:
    '''Converts a file into its corresponding .csv counterpart
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '_txt2csv.csv'
    with open(file, 'r', encoding='utf8') as f:
        text = ','.join([b.strip() for b in next(f).split('\t')]) + '\n'
        for line in f:
            ids, vals = line.split('\t')[0], line.split('\t')[1:]
            text = text + ids + ',' + ','.join(vals)
    write_file(file_name, CONVERTED_DIR_PATH, text)


def convert_to_txt(file: str) -> None:
    '''Converts a file into its corresponding .csv counterpart
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '_conv_tab.csv'
    with open(file, 'r', encoding='utf8') as f:
        text = '\t'.join([b.strip() for b in next(f).split(';')]) + '\n'
        for line in f:
            ids, vals = line.split(';')[0], line.split(';')[1:]
            text = text + ids + '\t' + '\t'.join(vals)
    write_file(file_name, CONVERTED_DIR_PATH, text)


def write_file(file: str, dir: str, string: str) -> None:
    '''Temp function for writing into a file
    '''
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(os.path.join(dir, file), 'w', encoding='utf8') as f:
        f.writelines(string)



if __name__ == "__main__":
    for raw_file in os.scandir(RAW_DATA_PATH):
        if raw_file.is_file():
            txt2csv(raw_file)
from email.encoders import encode_noop
import os
from paths import *


def convert(file: str) -> None:
    '''Converts a file into its corresponding .csv counterpart
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '_conv.csv'
    with open(file, 'r', encoding='utf8') as f:
        text = ',"' + '","'.join([b.strip()
                                 for b in next(f).split(';')][1:]) + '"\n'
        for line in f:
            ids, vals = line.split(';')[0], line.split(';')[1:]
            text = text + '"' + ids + '",' + ','.join(vals)
    write_file(file_name, CONVERTED_DIR_PATH, text)


def convert_to_csv(file: str):
    '''Converts a file into its corresponding .csv counterpart,
    data files from Proline are exported as comma separated, the rest
    of these script rely on semicolon separated files
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '_conv.csv'
    with open(file, 'r', encoding='utf8') as f:
        text = '#;' + ';'.join([s.strip().split(' ')[-1][0:-1] for s in next(f).split(',')[1:]]) + '\n'
        for line in f:
            ids, vals = line.split(',')[0], line.split(',')[1:]
            text = text +  ids[:-6] + ';' + ';'.join(vals)
    write_file(file_name, RAW_CSV_DATA_PATH, text)
    return os.path.join(RAW_CSV_DATA_PATH, file_name)


def convert_to_txt(file):
    '''Converts a csv file into txt format
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.txt'
    with open(file, 'r', encoding='utf8') as f:
        text = 'NAME\tDESCRIPTION\t' + \
            '\t'.join([s.strip() for s in next(f).split(';')][1:]) + '\n'
        for line in f:
            cells = line.split(';')
            text = text + '\t'.join([cells[0]] + ['na'] + cells[1:])
    write_file(file_name, TXT_DIR_PATH, text)


def convert_to_gct(file):
    '''Converts a csv file into gct format
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.gct'
    nproteins = 0
    with open(file, 'r', encoding='utf8') as f:
        header = next(f).split(';')
        nsamples = len(header) - 1
        text = 'NAME\tDESCRIPTION\t' + \
            '\t'.join([s.strip() for s in header][1:]) + '\n'
        for line in f:
            nproteins = nproteins + 1
            cells = line.split(';')
            text = text + '\t'.join([cells[0]] + ['na'] + cells[1:])
    text = f'#1.2\n{nproteins}\t{nsamples}\n' + text
    write_file(file_name, GCT_DIR_PATH, text)


def create_cls(file):
    '''Creates .cls file from a .csv obtained by running
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.cls'
    code_set = []
    with open(file, 'r', encoding='utf8') as f:
        header = next(f).split(';')
        samples = [s.strip() for s in header][1:]
        nsamples = len(samples)
        my_form = [-1] * nsamples
        for index, sample in enumerate(samples):
            code, _ = get_sample_code(sample)
            if code not in code_set:
                code_set = code_set + [code]
            my_form[index] = code
    my_form[-1] = my_form[-1].strip()
    my_form = f'{nsamples} {len(code_set)} 1\n# ' + \
        ' '.join(code_set) + '\n' + ' '.join(my_form)
    write_file(file_name, PHENOTYPES_DIR_PATH, my_form)


def write_file(file: str, dir: str, string: str) -> None:
    '''Temp function for writing into a file
    '''
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(os.path.join(dir, file), 'w', encoding='utf8') as f:
        f.writelines(string)


def get_sample_code(string: str) -> tuple:
    '''Obtains a sample code from a given string, which is given
    in a form of `CCCNNNNN`, where `C` is a character and `N` represents
    a number.
    '''
    index = 0
    for char in string.lstrip():
        if char not in '0123456789':
            index = index + 1
        else:
            break
    return (string[:index], string[index:])


if __name__ == "__main__":
    for raw_file in os.scandir(RAW_DATA_PATH):
        if raw_file.is_file():
            with open(raw_file, 'r', encoding='utf8') as text:
                if ',' in next(text):
                    raw_file = convert_to_csv(raw_file)
            convert(raw_file)
            create_cls(raw_file)
            convert_to_txt(raw_file)
            convert_to_gct(raw_file)

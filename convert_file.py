import os
from paths import *


def convert(file: str) -> None:
    '''Converts a file into its corresponding .csv counterpart
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '_conv.csv'
    with open(file, 'r') as f:
        text = ',"' + '","'.join([b.strip()
                                 for b in next(f).split(';')][1:]) + '"\n'
        for line in f:
            id, vals = line.split(';')[0], line.split(';')[1:]
            text = text + '"' + id + '",' + ','.join(vals)
    write_file(file_name, CONVERTED_DIR_PATH, text)


def convert_to_txt(file):
    file_name = os.path.splitext(os.path.basename(file))[0] + '.txt'
    with open(file, 'r') as f:
        text = 'NAME\tDESCRIPTION\t' + \
            '\t'.join([s.strip() for s in next(f).split(';')][1:]) + '\n'
        for line in f:
            cells = line.split(';')
            text = text + '\t'.join([cells[0]] + ['na'] + cells[1:])
    write_file(file_name, TXT_DIR_PATH, text)


def convert_to_gct(file):
    file_name = os.path.splitext(os.path.basename(file))[0] + '.gct'
    nproteins = 0
    with open(file, 'r') as f:
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
    with open(file, 'r') as f:
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
    my_form = f'{nsamples} {len(code_set)} 1\n' + '# ' + \
        ' '.join(code_set) + '\n' + ' '.join(my_form)
    write_file(file_name, PHENOTYPES_DIR_PATH, my_form)


def write_file(file: str, dir: str, string: str) -> None:
    if not os.path.exists(dir):
        os.makedirs(dir)
    with open(os.path.join(dir, file), 'w') as f:
        f.writelines(string)


def get_sample_code(string: str) -> tuple:
    index = 0
    for char in string.lstrip():
        if char not in '0123456789':
            index = index + 1
        else:
            break
    return (string[:index], string[index:])


if __name__ == "__main__":
    for file in os.scandir(RAW_DATA_PATH):
        if file.is_file():
            convert(file)
            create_cls(file)
            convert_to_txt(file)
            convert_to_gct(file)

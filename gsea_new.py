import os
from paths import *
from id_mapping import *


def convert(file: str) -> None:
    '''Converts a file into its corresponding .csv counterpart
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.gct'
    with open(file, 'r', encoding='utf8') as f:
        next(f)
        proteins = {}
        for line in f:
            dat = line.split(',')
            proteins[dat[0]] = dat[1:]
            # ids.append(line.split(',')[0])
    ids = list(proteins.keys())
    gene_names = get_gene_names(ids)
    protein_descriptions = get_prot_description(ids)
    protein_descriptions = {gene_names[protein]: protein_descriptions[protein] for protein in protein_descriptions if protein in gene_names.keys()}
    correct_names = [gene_names[id] for id in ids if id in gene_names.keys()]
    nproteins = 0
    text = ''
    with open(file, 'r', encoding='utf8') as f:
        header = next(f)
        nsamples = len(header.split(',')) - 1
        for line in f:
            if line.split(',')[0] in gene_names.keys():
                protein = correct_names[nproteins]
                text = text + f'{protein}\t{protein_descriptions[protein]}\t' + '\t'.join(line.strip().split(',')[1:]) + '\n'
                nproteins += 1
    header = 'NAME\tDescription\t' + '\t'.join([cell.split(' ')[-1] for cell in header.strip().split(',')[1:]]) + '\n'
    text = '#1.2\n' + f'{nproteins}\t{nsamples}\n' + header + text
    write_file(file_name, GCT_DIR_PATH, text)
    

    # print(gene_names['PHB_HUMAN'])
    # print(protein_descriptions)
    # print(len(correct_names))
    # print(len(ids))




# def convert_to_txt(file):
#     '''Converts a csv file into txt format
#     '''
#     file_name = os.path.splitext(os.path.basename(file))[0] + '.txt'
#     with open(file, 'r', encoding='utf8') as f:
#         text = 'NAME\tDESCRIPTION\t' + \
#             '\t'.join([s.strip() for s in next(f).split(',')][1:]) + '\n'
#         for line in f:
#             cells = line.split(',')
#             text = text + '\t'.join([cells[0]] + ['na'] + cells[1:])
#     write_file(file_name, TXT_DIR_PATH, text)


def convert_to_gct(file):
    '''Converts a csv file into gct format
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.gct'
    nproteins = 0
    with open(file, 'r', encoding='utf8') as f:
        header = next(f).split(',')
        nsamples = len(header) - 1
        text = 'NAME\tDESCRIPTION\t' + \
            '\t'.join([s.strip() for s in header][1:]) + '\n'
        for line in f:
            nproteins = nproteins + 1
            cells = line.split(',')
            text = text + '\t'.join([cells[0]] + ['na'] + cells[1:])
    text = f'#1.2\n{nproteins}\t{nsamples}\n' + text
    write_file(file_name, GCT_DIR_PATH, text)


def create_cls(file):
    '''Creates .cls file from a .csv obtained by running Proline
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.cls'
    code_set = []
    with open(file, 'r', encoding='utf8') as f:
        header = next(f).split(',')
        samples = [s.strip().split(' ')[-1] for s in header[1:]]
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
            convert(raw_file)
            create_cls(raw_file)

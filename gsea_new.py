import os
from paths import *
from id_mapping import *


def convert(file: str) -> None:
    '''Creates a .gct file suitable for inputting into the GSEA software.

    Parameters:
    `file`: path of the file to be transformed
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.gct'
    with open(file, 'r', encoding='utf8') as f:
        # vytvori header (3. riadok v spravnom formate)
        header = 'NAME\tDescription\t' + \
            '\t'.join([s.split(' ')[-1].strip()
                      for s in next(f).split(',')[1:]]) + '\n'
        
        # pocet vzoriek, ktore su v subore, napr. (Z1, Z2, ...)
        nsamples = len(header.split('\t')) - 2

        # vytovrenie dict nameranych hodnot pre jednotlive proteiny
        proteins = {}
        for line in f:
            dat = line.split(',')
            proteins[dat[0]] = '\t'.join([str(val) for val in dat[1:]]).strip()
    ids = list(proteins.keys())

    # ziskanie Gene_Name a popis jednotlivych proteinov pomocou API UniProt-u
    gene_names = get_gene_names(ids)
    protein_descriptions = get_prot_description(ids)
    protein_descriptions = {gene_names[protein]: protein_descriptions[protein]
                            for protein in protein_descriptions if protein in gene_names.keys()}

    # filtrovanie pre proteiny, ktore sa nasli v UniProt-e a ich pocet
    correct_names = [gene_names[id] for id in ids if id in gene_names.keys()]
    nproteins = len(correct_names)

    # formatovanie dat o jednotlivych proteinoch a nasledne spojenie s header-om a dalsim popisom
    text = '\n'.join([gene_names[prot] + '\t' + protein_descriptions[gene_names[prot]] +
                     '\t' + proteins[prot] for prot in proteins if prot in gene_names.keys()])
    text = '#1.2\n' + f'{nproteins}\t{nsamples}\n' + header + text

    # zapis do suboru
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

import os
from paths import *
from id_mapping import *
from datetime import date


def convert(file: str, name_choice: int) -> None:
    '''Creates a .gct file suitable for inputting into the GSEA software.

    Parameters:
    `file`: path of the file to be transformed
    '''
    with open(file, 'r', encoding='utf8') as f:
        # vytvori header (3. riadok v spravnom formate) - NAMe'\t'Description'\t'Oznacenia vzoriek
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

    # ziskanie Gene_Name alebo KEGG ID (podla vyberu) a popis jednotlivych proteinov pomocou API UniProt-u
    if name_choice == 2:
        gene_names = get_gene_names(ids)
    else:
        gene_names = get_kegg_ids(ids)

    protein_descriptions = get_prot_description(ids)
    new_names = gene_names.keys()

    
    volba = "KEGG ID" if name_choice != 2 else "Gene Name"
    file_name = os.path.splitext(os.path.basename(file))[0] + f'{volba[:4]}.gct'
    log_file = os.path.splitext(os.path.basename(file))[0] + f'{volba[:4]}.log'
    # logovanie prosteinov, ktore sa nanasli v KEGG / Gene Name
    print(f'{volba} sa nenaslo pre tieto proteiny ({len(set(ids) - set(new_names))} z celkoveho poctu {len(ids)}):')
    if not os.path.exists(LOG_DIR_PATH):
        os.makedirs(LOG_DIR_PATH)
    with open(os.path.join(LOG_DIR_PATH, log_file), 'w', encoding='utf8') as f:
        f.write(f'---------------------------------------------------------\n {os.path.splitext(os.path.basename(file))[0]}\n---------------------------------------------------------\n')
        f.write(f'{volba} sa nenaslo pre tieto proteiny ({len(set(ids) - set(new_names))} z celkoveho poctu {len(ids)}):\n')
        for protein in ids:
            if protein not in new_names:
                print(protein)
                f.writelines(protein + '\n')
        f.write('---------------------------------------------------------')

    protein_descriptions = {gene_names[protein]: protein_descriptions[protein]
                            for protein in protein_descriptions if protein in new_names}
    # filtrovanie pre proteiny, ktore sa nasli v UniProt-e a ich pocet
    correct_names = [gene_names[id] for id in ids if id in new_names]
    nproteins = len(correct_names)

    # formatovanie dat o jednotlivych proteinoch a nasledne spojenie s header-om a dalsim popisom
    text = '\n'.join([gene_names[prot] + '\t' + protein_descriptions[gene_names[prot]] +
                     '\t' + proteins[prot] for prot in proteins if prot in new_names])
    text = '#1.2\n' + f'{nproteins}\t{nsamples}\n' + header + text

    # zapis do suboru
    write_file(file_name, os.path.join(GCT_DIR_PATH, str(date.today())), text)


def create_cls(file):
    '''Creates .cls file from a .csv obtained by running Proline
    '''
    file_name = os.path.splitext(os.path.basename(file))[0] + '.cls'
    code_set = []
    with open(file, 'r', encoding='utf8') as f:
        header = next(f).split(',')

        # delenie na subory pre 'mess' (vzorky nie su zmergovane podla jednotlivych merani) a normalny postup,resp. naopak
        if '_' not in header[1]:
            samples = [s.strip().split(' ')[-1] for s in header[1:]]
        else:
            samples = [s.strip().split(' ')[-1].split('_')[2] if 'z' in s else s.strip().split(' ')[-1].split('_')[1] for s in header[1:]]
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
    write_file(file_name, os.path.join(PHENOTYPES_DIR_PATH, str(date.today())), my_form)


def write_file(file: str, direct: str, string: str) -> None:
    '''Temp function for writing into a file
    '''
    if not os.path.exists(direct):
        os.makedirs(direct)
    with open(os.path.join(direct, file), 'w', encoding='utf8') as f:
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


def semi2comma(file: str):
    '''Detects if `file` has semicolons instead of commas and changes to
    true .csv format accordingly
    '''
    with open(file, 'r', encoding='utf8') as f:
        file_content = f.readlines()
        if ';' in file_content[0]:
            new_string = ''.join([','.join(row.split(';')) for row in file_content])
        else:
            new_string = file_content
    write_file(file, RAW_DATA_PATH, new_string)
    


if __name__ == "__main__":
    choice = int(input('KEGG (1) / Gene Name (2): '))
    for raw_file in os.scandir(RAW_DATA_PATH):
        if raw_file.is_file():
            print(f'Spracovavam {str(raw_file)[11:-2]}')
            semi2comma(raw_file)
            convert(raw_file, choice)
            time.sleep(1)
            create_cls(raw_file)

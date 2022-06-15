
import os
from string import digits


def convert(file):
    lines = open(file, "r")
    text = ''
    for line in lines:
        cells = line.split(',')
        if line[0] == ',':
            for i in range(1, len(cells) - 1):
                cells[i] = '"' + cells[i] + '"'
            cells[-1] = '"' + cells[-1][:-1] + '"\n'
        else:
            cells[0] = '"' + cells[0] + '"'
        text = text + ','.join(cells)
    lines.close()
    new_dir = os.path.join(os.path.dirname(file), 'converted')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    output = open(os.path.join(new_dir, f'{file}'[11:-6] + '_conv.csv'), 'w')
    output.writelines(text)
    output.close()


def convert_to_txt(file):
    with open(file, 'r') as f:
        text = 'NAME\tDESCRIPTION\t' + \
            '\t'.join([s.strip() for s in next(f).split(';')][1:]) + '\n'
        for line in f:
            cells = line.split(';')
            text = text + '\t'.join([cells[0]] + ['na'] + cells[1:]) + '\n'
        new_dir = os.path.join(os.path.dirname(file), 'txt')
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        output = open(os.path.join(new_dir, f'{file}'[11:-6] + '.txt'), 'w')
        output.writelines(text)
        output.close()


def create_cls(file):
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
            my_form[index] = code + ' '
    my_form[-1] = my_form[-1].strip()
    new_dir = os.path.join(os.path.dirname(file), 'phenotypes')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    output = open(os.path.join(new_dir, f'{file}'[11:-6] + '.cls'), 'w')
    output.writelines(f'{nsamples} {len(code_set)} 1\n')
    output.writelines('# ' + ' '.join(code_set) + '\n')
    output.writelines(my_form)
    output.close()



# Povody script na .cls subory z .csv
#
# def create_cls(file):
#     code_set = []
#     with open(file, 'r') as fajl:
#         for line in fajl:
#             samples = line.split(',')[1:-1] + [line.split(',')[-1][:-1]]
#             nsamples = len(samples)
#             my_form = [-1] * nsamples
#             for index, sample in enumerate(samples):
#                 code, _ = get_sample_code(sample)
#                 if code not in code_set:
#                     code_set = code_set + [code]
#                 my_form[index] = code + ' '
#             break
#     my_form[-1] = my_form[-1].strip()
#     new_dir = os.path.join(os.path.dirname(file), 'phenotypes')
#     if not os.path.exists(new_dir):
#         os.makedirs(new_dir)
#     output = open(os.path.join(new_dir, f'{file}'[11:-6] + '.cls'), 'w')
#     output.writelines(f'{nsamples} {len(code_set)} 1\n')
#     output.writelines('# ' + ' '.join(code_set) + '\n')
#     output.writelines(my_form)
#     output.close()


def get_sample_code(string: str) -> tuple:
    index = 0
    for char in string.lstrip():
        if char not in digits:
            index = index + 1
        else:
            break
    return (string[:index], string[index:])


if __name__ == "__main__":
    directory = 'data_3'
    for file in os.scandir(directory):
        if file.is_file():
            convert(file)
            create_cls(file)
            convert_to_txt(file)

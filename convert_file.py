
from heapq import nsmallest
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


def create_cls(file):
    with open(file, 'r') as fajl:
        idx = 0
        code_set = []
        for line in fajl:
            idx = idx + 1
            if idx > 1:
                break
            samples = line.split(',')[1:-1] + [line.split(',')[-1][:-1]]
            nsamples = len(samples)
            my_form = [-1] * nsamples
            for index, sample in enumerate(samples):
                code = get_sample_code(sample)
                if code not in code_set:
                    code_set = code_set + [code]
                # code_set.add(code)
                my_form[index] = code + ' '

                # if sample.lstrip()[0] == 'K':
                #     my_form[idx] = 'K '
                # else:
                #     my_form[idx] = 'P '
    new_dir = os.path.join(os.path.dirname(file), 'phenotypes')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    output = open(os.path.join(new_dir, f'{file}'[11:-6] + '.cls'), 'w')
    output.writelines(f'{nsamples} {len(code_set)} 1\n')
    output.writelines('# ' + ' '.join(code_set) + '\n')
    output.writelines(my_form)
    output.close()



def get_sample_code(string: str) -> str:
    tmp = ''
    for char in string.lstrip():
        if char not in digits:
            tmp = tmp + char
        else: break
    return tmp



if __name__ == "__main__":
    directory = 'Data_2'
    for file in os.scandir(directory):
        if file.is_file():
            convert(file)
            create_cls(file)

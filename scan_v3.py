import xlrd
import os


tab = {}


def scan_file(name):
    loc = (name)
    wb = xlrd.open_workbook(loc)
    sheet = wb.sheet_by_index(0)
    for i in range(1, sheet.nrows):
        p_name = sheet.cell_value(i, 4)
        p_count = int(sheet.cell_value(i, 9))
        if p_name in tab:
            tab[p_name][0] = tab[p_name][0] + p_count
            tab[p_name][1].append(i)
        else:
            tab[p_name] = [p_count, [i]]


def check_occurance(name: str) -> int:
    return len(tab[name][1])


def avg_placing(name: str) -> float:
    return sum(tab[name][1]) / check_occurance(name)


def avg_count(name: str) -> float:
    return tab[name][0] / check_occurance(name)


def top_n(name: str, n: int) -> int:
    return len([1 for i in range(check_occurance(name)) if tab[name][1][i] <= n])


if __name__ == "__main__":
    dictionary = 'Data'
    for file in os.scandir(dictionary):
        if file.is_file():
            scan_file(file)
    sorted_proteins = sorted(tab.items(), key=lambda x: x[1], reverse=True)
    result_file = open('results.txt', 'w')
    for item in sorted_proteins:
        result_file.write(f'{item[0]}\t\t\t{item[1]}\n')
    result_file.close()
    print(top_n("Vimentin OS=Homo sapiens OX=9606 GN=VIM PE=1 SV=4", 2))

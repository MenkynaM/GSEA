import xlrd, os


global_tab = {}

def scan_file(name):
    loc = (name)
    wb = xlrd.open_workbook(loc)
    sheet = wb.sheet_by_index(0)
    tab = {}
    for i in range(1, sheet.nrows):
        tab[sheet.cell_value(i, 4)] = int(sheet.cell_value(i, 9))
    return tab

def add_to_global(tab):
    for key in tab:
        if key in global_tab:
            global_tab[key] = global_tab[key] + tab[key]
        else:
            global_tab[key] = tab[key]
    


if __name__ == "__main__":
    dictionary = 'Data'
    for file in os.scandir(dictionary):
        if file.is_file():
            add_to_global(scan_file(file))
    sorted_proteins = sorted(global_tab.items(), key=lambda x: x[1], reverse=True)
    result_file = open('results.txt', 'w')
    for item in sorted_proteins:
        result_file.write('{0} \t\t\t {1}\n'.format(item[0], item[1]))
    result_file.close()
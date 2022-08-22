import xlrd, os

class Protein:
    def __init__(self, name: str, count: int, placing: list) -> None:
        self.name = name
        self.count = count
        self.placing = placing


proteins = []

def scan_file(name: str) -> None:
    """
        Scan a single file
    """
    loc = (name)
    wb = xlrd.open_workbook(loc)
    sheet = wb.sheet_by_index(0)

    for i in range(1, sheet.nrows):
        protein_name = sheet.cell_value(i, 4)
        protein_count = int(sheet.cell_value(i, 9))
        if len(proteins) == 0:
            proteins.append(Protein(protein_name, protein_count, [i]))
            continue
        # print(f'{protein_name} - {protein_count}')
        for protein in proteins:
            if protein_name == protein.name:
                # print('som tam')
                protein.count += protein_count
                protein.placing.append(i)
            else:
                # print('som tu')
                proteins.append(Protein(protein_name, protein_count, [i]))
        # tab[sheet.cell_value(i, 4)] = int(sheet.cell_value(i, 9))

# def add_to_global(tab):
#     for key in tab:
#         if key in global_tab:
#             global_tab[key] = global_tab[key] + tab[key]
#         else:
#             global_tab[key] = tab[key]
    


if __name__ == "__main__":
    dictionary = 'Data'
    for file in os.scandir(dictionary):
        if file.is_file():
            scan_file(file)
    # sorted_proteins = sorted(global_tab.items(), key=lambda x: x[1], reverse=True)
    result_file = open('results.txt', 'w')
    for protein in proteins:
        result_file.write(f'{protein.name} \t\t\t {protein.count}')
        # result_file.write('{0} \t\t\t {1}\n'.format(protein.name, protein.count))
    result_file.close()
    print(proteins)
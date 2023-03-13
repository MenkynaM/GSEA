import os


def read_data(file: str) -> dict:
    with open(file, 'r', encoding='utf8') as f:
        header = next(f)
        d = {line.split(',')[0]: line.strip().split(',')[2:] for line in f.readlines()}
    return d


def filter_data(data: dict) -> dict:
    return {k: v for k, v in data.items() if float(v[-4]) < 0.05 and abs(float(v[-3])) > 1.5}


orig_path = os.getcwd()
os.chdir(r"C:\Users\admin\Documents\data")
files = [item for item in os.walk('.')]
print(files)
print(filter_data(read_data(r"C:\Users\admin\Documents\data\TNBC\updownCD4.csv")))

import os, shutil

files = [file for file in os.walk('D:\\vysledky_marika\\COVID_mesiac po ochorení_kontrola\\') if file[-1] and file[-1][0].endswith('.dat')]
root_dir = r'C:\Users\Menkyna\Documents\DATA_vyskum\raw_data\COVID_kontrola'
# if
counter = 0
for file in files:
    os.chdir(root_dir)
    original_name = file[2][0]
    path_to_original_file = file[0]
    info = file[0].split('\\') + [original_name[:-4]]
    znak = info[4]
    new_name = '_'.join([znak, info[3], info[-1], info[6][0]]) + '.dat'
    
    os.chdir(os.path.join(os.getcwd(), znak))
    # print(os.path.join(path_to_original_file, original_name), new_name)
    # cmd = f'copy {os.path.join(path_to_original_file, original_name)} {new_name}'
    shutil.copy2(os.path.join(path_to_original_file, original_name), new_name)
    counter = counter + 1
    print(f'{counter/len(files)*100}\%', flush=True)
    # os.system(cmd)

    
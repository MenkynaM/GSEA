import os
from datetime import datetime

now = datetime.now()

DATA_DIR = os.path.join(os.getcwd(), 'data')

GCT_DIR_PATH = os.path.join(DATA_DIR, 'gct')
CHIPS_DIR_PATH = os.path.join(DATA_DIR, 'chips')
GMT_DIR_PATH = os.path.join(DATA_DIR, 'gmt')
CONVERTED_DIR_PATH = os.path.join(DATA_DIR, 'converted')
PHENOTYPES_DIR_PATH = os.path.join(DATA_DIR, 'phenotypes')
TXT_DIR_PATH = os.path.join(DATA_DIR, 'txt')
RAW_DATA_PATH = os.path.join(DATA_DIR, 'raw')
RAW_CSV_DATA_PATH = os.path.join(DATA_DIR, 'csv')
KEGG_DATA_PATH = os.path.join(DATA_DIR, 'kegg')
PROLINE_RAW_DATA_PATH = os.path.join(DATA_DIR, 'proline_raw')
LOG_DIR_PATH = os.path.join(DATA_DIR, 'log')
CHIP_DL_URL = 'https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/'
GSEA_OUTPUT_PATH = [os.path.join(direc, 'gsea_home', 'output', str(now.year)) for direc in os.scandir(
    'C:\\Users') if direc.is_dir() and (' Use' not in direc.path) and ('Public' not in direc.path) and ('Defa' not in direc.path)][0]


# WINDOWS
if os.name == 'nt':
    gsea_dicts = [y for y in [os.path.abspath(x) for x in os.scandir(
        os.environ['ProgramFiles'])] if 'GSEA' in y]
    if len(gsea_dicts) == 1:
        GSEA_PATH = gsea_dicts[0]
    else:
        print('Multiple GSEA installations found, choose one:')
        print('\n'.join('{} - {}'.format(*k) for k in enumerate(gsea_dicts)))
        GSEA_PATH = gsea_dicts[int(input('Type the label number: '))]
    del gsea_dicts

    # GSEA_PATH = [y for y in [os.path.abspath(x) for x in os.scandir(os.environ['ProgramFiles'])] if 'GSEA' in y][0]
# LINUX
if os.name == 'posix':
    GSEA_PATH = os.path.abspath(os.path.join('..', 'GSEA_4.2.3'))


def select_dir(path: str):
    """
    Choose a directory to change into from a list
    """
    dirs = [direc for direc in os.scandir(path) if direc.is_dir()]
    print('\n'.join(f'{k[0]}\t- {str(k[1])[11:-2]}' for k in enumerate(dirs)))
    # print('\n'.join('{}\t- {}'.format(*k) for k in enumerate(dirs)))
    return os.path.join(path, dirs[int(input('Choose a dir: '))])

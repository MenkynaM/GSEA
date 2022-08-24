import enum
import os

GCT_DIR_PATH = os.path.join(os.getcwd(), 'data', 'gct')
CHIPS_DIR_PATH = os.path.join(os.getcwd(), 'data', 'chips')
GMT_DIR_PATH = os.path.join(os.getcwd(), 'data', 'gmt')
CONVERTED_DIR_PATH = os.path.join(os.getcwd(), 'data', 'converted')
PHENOTYPES_DIR_PATH = os.path.join(os.getcwd(), 'data', 'phenotypes')
TXT_DIR_PATH = os.path.join(os.getcwd(), 'data', 'txt')


# WINDOWS
if os.name == 'nt':
    gsea_dicts = [y for y in [os.path.abspath(x) for x in os.scandir(os.environ['ProgramFiles'])] if 'GSEA' in y]
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

CHIP_DL_URL = 'https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/'
import os
import subprocess
import requests
from bs4 import BeautifulSoup
from paths import *


execution_file = 'gsea-cli.sh' if os.name == 'posix' else 'gsea-cli.bat'


DEFAULT_SETTINGS = [
    execution_file,            'GSEA',
    '-zip_report',              'false',
    '-num',                     '100',
    '-scoring_scheme',          'weighted',
    '-norm',                    'meandiv',
    '-mode',                    'Max_probe',
    '-include_only_symbols',    'true',
    '-set_max',                 '500',
    '-plot_top_x',              '50',
    '-nperm',                   '1000',
    '-order',                   'descending',
    '-rnd_seed',                'timestamp',
    '-rpt_label',               'my_analysis',
    '-set_min',                 '10',
    '-create_svgs',             'false',
    '-sort',                    'real',
    '-create_gcts',             'false',
    '-save_rnd_lists',          'false',
    '-median',                  'false',
    '-metric',                  'Signal2Noise',
    '-make_sets',               'true',
    '-rnd_type',                'no_balance',
    '-permute',                 'phenotype',
    '-collapse',                'Collapse',
    '-out',                     os.path.join(os.getcwd(), 'data', 'gsea')
]


def run_gsea(src: str, cls: str, gmx: str, chip: str) -> None:
    '''Run a single instance of GSEA with selected files
    as inputs
    '''
    old_dir = os.getcwd()
    os.chdir(GSEA_PATH)
    subprocess.run(DEFAULT_SETTINGS +
                   ['-res', src, '-cls', cls, '-gmx', gmx, '-chip', chip], shell=True)
    os.chdir(old_dir)


def get_file_list(url=CHIP_DL_URL) -> list:
    '''Opens `https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/`
    to search for all Human_*.chip files and returns their list
    '''

    # open `url` and search for all `<a>` elements
    url_new = requests.get(url).text
    soup = BeautifulSoup(url_new, 'html.parser')
    tmp = soup.select('a')

    # get their link attributes and return in the form of a list
    return [elem.attrs['href'] for elem in tmp if elem.text.startswith('H')]


def download_files(lst: list, url: str) -> None:
    '''Download the files listed in `lst` from `url`
    '''

    # create new directory, if nonexistent, and change there
    if not os.path.exists(CHIPS_DIR_PATH):
        os.makedirs(CHIPS_DIR_PATH)
    os.chdir(CHIPS_DIR_PATH)

    # download all `*.chip` files from `lst` in `url`
    # WINDOWS
    if os.name == 'nt':
        for item in lst:
            os.system('curl -o ' + item + ' ' + url + item)

    # LINUX
    if os.name == 'posix':
        for item in lst:
            os.system('wget ' + url + item)

    # change the directory back
    os.chdir('../..')


if __name__ == '__main__':
    chips = [os.path.abspath(file) for file in os.scandir(CHIPS_DIR_PATH)]
    gmts = [os.path.abspath(file) for file in os.scandir(GMT_DIR_PATH)]
    src_file = os.path.abspath(os.path.join(GCT_DIR_PATH, 'skuska.gct'))
    cls_file = os.path.abspath(os.path.join(PHENOTYPES_DIR_PATH, 'skuska.pcl')) + '#P_versus_K'
    
    # print('\n'.join('{} - {}'.format(*k) for k in enumerate(gmts)))

    # print(GSEA_PATH)
    # download_files(get_file_list(), CHIP_DL_URL)
    run_gsea(src_file, cls_file, gmts[9], chips[29])
    # for chip in chips:
    #     for gmt in gmts:
    #         run_gsea(src_file, cls=cls_file, gmx=gmt, chip=chip)

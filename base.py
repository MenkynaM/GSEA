import os
import subprocess
import requests
from bs4 import BeautifulSoup


DEFAULT_SETTINGS = [
    './gsea-cli.sh',            'GSEA',
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
    '-rnd_seed',                '143',
    '-rpt_label',               'my_analysis',
    '-set_min',                 '10',
    '-create_svgs',             'true',
    '-sort',                    'real',
    '-create_gcts',             'true',
    '-save_rnd_lists',          'false',
    '-median',                  'false',
    '-metric',                  'Signal2Noise',
    '-make_sets',               'true',
    '-rnd_type',                'no_balance',
    '-permute',                 'gene_set',
    '-collapse',                'Collapse',
]


def run_gsea(src: str, cls: str, gmx: str, chip: str) -> None:
    '''Run a single instance of GSEA with selected files
    as inputs
    '''
    old_dir = os.getcwd()
    os.chdir('/home/menkyna/Downloads/GSEA_Linux_4.2.3')
    subprocess.run(DEFAULT_SETTINGS +
                   ['-res', src, '-cls', cls, '-gmx', gmx, '-chip', chip])
    os.chdir(old_dir)


def get_file_list(url: str) -> list:
    '''Opens `https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/`
    to search for all Human_*.chip files and returns their list
    '''

    # open `url` and search for all `<a>` elements
    url_new = requests.get(url).text
    soup = BeautifulSoup(url_new, 'html.parser')
    tmp = soup.select('a')

    # get their link attributes and return in the form of a list
    a = [elem.attrs['href'] for elem in tmp if elem.text.startswith('H')]
    return a


def download_files(lst: list, url: str) -> None:
    '''Download the files listed in `lst` from `url`
    '''

    # create new directory, if nonexistent, and change there
    new_dir = os.path.join(os.getcwd(), 'data', 'chips')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    os.chdir(new_dir)

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
    url = 'https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/'
    # lst = get_file_list(url)
    # lst = [item for item in get_file_list(url) if '7.5.1' in item]
    # download_files(lst, url)
    chips = [os.path.abspath(file) for file in os.scandir('data/chips')]
    gmts = [os.path.abspath(file) for file in os.scandir('data/gmt')]
    src_file = os.path.abspath('data/gct/skuska.gct')
    cls_file = os.path.abspath('data/phenotypes/skuska.cls') + '#K_versus_P'
    # print(cls_file)
    
    # run_gsea(src_file, cls_file, gmts[0], chips[0])
    for chip in chips:
        for gmt in gmts:
            run_gsea(src_file, cls=cls_file, gmx=gmt, chip=chip)

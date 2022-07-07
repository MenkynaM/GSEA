import os
from bs4 import BeautifulSoup
import requests

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
    lst = get_file_list(url)
    download_files(lst, url)
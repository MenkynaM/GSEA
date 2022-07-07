import os
from bs4 import BeautifulSoup
import requests

def get_file_list(url: str) -> list:
    '''Opens `https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/`
    to search for all Human_*.chip files and returns their list
    '''
    url = requests.get(url).text
    soup = BeautifulSoup(url, 'html.parser')
    tmp = soup.select('a')
    a = []
    for elem in tmp:
        if elem.text.startswith('H'):
            a.append('https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/' + elem.attrs['href'])
    return a




if __name__ == '__main__':
    print(get_file_list('https://data.broadinstitute.org/gsea-msigdb/msigdb/annotations_versioned/'))
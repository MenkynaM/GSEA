import os
from bs4 import BeautifulSoup
import csv
from paths import *


def scrape_file(dir: str, file: str) -> None:
    '''Extract a enrichment table from a single pathway file.

    Searches .htlm file using BeautifulSoup to find a table of enrichment
    results which are then extracter into a .csv file.
    '''

    # load <name of pathway>.html file into BS parser
    contents = open(os.path.join(dir, f'{file}.html'), 'r').read()
    soup = BeautifulSoup(contents, 'html.parser')

    #find the enrichment result table and read the header
    div = soup.select('.richTable')[0]
    head = [col.text for col in div.select('th')[1:]]

    # check if <dir>/converted exists, else create it
    new_dir = os.path.join(dir, 'converted')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    new_path = os.path.join(new_dir, f'{file}'[:-4] + '.csv')

    # read the rest of the table and write into a new file with the
    # same name except for the extension
    with open(new_path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(head)
        for row in div.select('tr'):
            writer.writerow([col.text.replace('"', '') for col in row.select('td')[1:]])


def scrape_index(file: str) -> None:
    '''Function for extracting list of gene sets that might interesting to us
    '''

    # find all of the entries and open the corresponding .html files, parsing
    # them using the `scrape_file` function
    cnts = open(file).read()
    soup = BeautifulSoup(cnts, 'html.parser')
    link = soup.select('a')[1].attrs['href']
    cnts = open(os.path.join(os.path.dirname(file), link)).read()
    soup = BeautifulSoup(cnts, 'html.parser')
    files = [cell.text for cell in soup.select('a')[::2]][:-1]
    for f in files:
        scrape_file(os.path.dirname(file), f)


def scrape_for_score(file: str) -> int:
    cnts = open(file).read()
    soup = BeautifulSoup(cnts, 'html.parser')
    lst = str(soup.select('li')[0]) 
    return int(lst.split(' ')[9][12:])
    


def find_files(filename: str) -> None:
    '''Searches for any file named `index.html` and parses them using `scrape_index` function
    '''
    result = []
    for root, _, files in os.walk(os.getcwd()):
        if filename in files:
            result.append(os.path.join(root, filename))
    return result




if __name__ == '__main__':
    index_list = find_files('index.html')
    dic = {}
    for file in index_list:
        dic[os.path.basename(file)] = scrape_for_score(file)
        # scrape_index(file)
    print(dic)

import os
from bs4 import BeautifulSoup
import csv

def scrape_file(file):
    pth = os.path.join(os.getcwd(), 'data', 'gsea')
    contents = open(os.path.join(pth, file), 'r').read()
    soup = BeautifulSoup(contents, 'html.parser')


    div = soup.select('.richTable')[0]
    head = [col.text for col in div.select('th')[1:]]
    new_dir = os.path.join(pth, 'converted')
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    new_path = os.path.join(pth, 'converted', f'{file}'[:-4] + 'csv')
    with open(new_path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(head)
        for row in div.select('tr'):
            writer.writerow([col.text.replace('"', '') for col in row.select('td')[1:]])


def get_pathway_list():
    cnts = open(os.path.join(os.getcwd(), 'data', 'gsea', 'index.html')).read()
    soup = BeautifulSoup(cnts, 'html.parser')
    link = soup.select('a')[1].attrs['href']
    cnts = open(os.path.join(os.getcwd(), 'data', 'gsea', link)).read()
    soup = BeautifulSoup(cnts, 'html.parser')
    return [cell.text for cell in soup.select('a')[::2]][:-1]
    # for file in link:
    #     scrape_file(file + '.html')
    # print([cell.text for cell in soup.select('a')])
    



if __name__ == '__main__':
    # scrape_file('REACTOME_FORMATION_OF_THE_CORNIFIED_ENVELOPE.html')
    flist = get_pathway_list()
    for file in flist:
        scrape_file(file + '.html')

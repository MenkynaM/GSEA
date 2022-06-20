from bs4 import BeautifulSoup
import csv

contents = open('data/gsea/REACTOME_FORMATION_OF_THE_CORNIFIED_ENVELOPE.html', 'r').read()
soup = BeautifulSoup(contents, 'html.parser')


div = soup.select('.richTable')[0]
head = [col.text for col in div.select('th')[1:]]
print(head)
for row in div.find_all('tr'):
    print([col.text for col in row.select('td')[1:]])

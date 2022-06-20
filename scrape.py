import os
from bs4 import BeautifulSoup
import csv

contents = open(os.path.join(os.getcwd(), 'data', 'gsea', 'REACTOME_FORMATION_OF_THE_CORNIFIED_ENVELOPE.html'), 'r').read()
soup = BeautifulSoup(contents, 'html.parser')


div = soup.select('.richTable')[0]
head = [col.text for col in div.select('th')[1:]]
with open('test.csv', 'w', encoding='UTF8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(head)
    for row in div.select('tr'):
        writer.writerow([col.text for col in row.select('td')[1:]])

# print(head)
# print(len(list(div.find_all('tr'))))
# for row in div.find_all('tr'):
    # print([col.text for col in row.select('td')[1:]])

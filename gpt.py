import requests

def get_gene_name(uniprot_id):
    url = f"https://www.uniprot.org/uniprot/{uniprot_id}.txt"
    response = requests.get(url)
    
    if response.ok:
        data = response.text
        lines = data.split('\n')
        
        for line in lines:
            if line.startswith('GN   Name='):
                gene_name = line.split('=')[1].split()[0]
                return gene_name
    
    return None

# Example usage
uniprot_ids = ['P12345', 'MYH9_HUMAN', 'O87654']

for uniprot_id in uniprot_ids:
    gene_name = get_gene_name(uniprot_id)
    if gene_name:
        print(f"UniProt ID: {uniprot_id} | Gene Name: {gene_name}")
    else:
        print(f"UniProt ID: {uniprot_id} | Gene Name not found")

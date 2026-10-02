"""Small inputs shared between test modules."""

from __future__ import annotations

#: A Proline export: decorated headers, UniProt entry names, comma separated.
PROLINE_CSV = (
    "Protein Set,norm(Weighted SC Z1),norm(Weighted SC Z2),norm(Weighted SC C1)\n"
    "MYH9_HUMAN,87.5,79.9,145.2\n"
    "FLNA_HUMAN,29.7,17.4,56.1\n"
    "ALBU_HUMAN,4.3,11.1,21.4\n"
)

#: The staged intermediate: bare sample names, semicolon separated.
STAGED_CSV = "#;Z1;Z2;C1\nMYH9;87.5;79.9;145.2\nFLNA;29.7;17.4;56.1\n"

#: An index.html of the shape GSEA writes, with its unclosed <li> tags.
GSEA_INDEX_HTML = """<html><body>
<div><h4>Enrichment in phenotype: <b>P (10 samples)</b></h4><ul>
<li>4 / 19 gene sets are upregulated in phenotype <b>P</b>
<li>0 gene sets are significant at FDR &lt; 25%
<li>0 gene sets are significantly enriched at nominal pvalue &lt; 1%
<li>1 gene sets are significantly enriched at nominal pvalue &lt; 5%
</ul></div>
<div><h4>Enrichment in phenotype: <b>K (10 samples)</b></h4><ul>
<li>15 / 19 gene sets are upregulated in phenotype <b>K</b>
<li>2 gene sets are significantly enriched at FDR &lt; 25%
<li>1 gene sets are significantly enriched at nominal pvalue &lt; 1%
<li>2 gene sets are significantly enriched at nominal pvalue &lt; 5%
</ul></div>
</body></html>
"""

#: A gene set detail page, cut down to its enrichment table.
GENE_SET_HTML = """<html><body>
<div class='keyValTable'><table><th></th><th></th>
<tr><td>GeneSet</td><td>HALLMARK_COAGULATION</td></tr></table></div>
<div class='richTable'><table cols='4' border='1'>
<th class='richTable'></th><th class='richTable'>SYMBOL</th>
<th class='richTable'>TITLE</th><th class='richTable'>CORE ENRICHMENT</th>
<tr><td class='lessen'>1</td><td><a href='https://ensembl.org/x?q=HRG'>HRG</a></td>
<td>histidine rich glycoprotein</td><td bgcolor='#CCFFCC'>Yes</td></tr>
<tr><td class='lessen'>2</td><td><a href='https://ensembl.org/x?q=APOA1'>APOA1</a></td>
<td>"apolipoprotein A1, variant"</td><td>No</td></tr>
</table></div></body></html>
"""

#: A per-phenotype report page, whose links name the gene set detail pages.
GSEA_REPORT_HTML = """<html><body><div class='richTable'><table>
<th></th><th>GS</th><th>GS DETAILS</th>
<tr><td>1</td>
<td><a href='http://www.gsea-msigdb.org/x/HALLMARK_COAGULATION'>HALLMARK_COAGULATION</a></td>
<td><a href='HALLMARK_COAGULATION.html'>Details ...</a></td></tr>
<tr><td>2</td>
<td><a href='http://www.gsea-msigdb.org/x/HALLMARK_HYPOXIA'>HALLMARK_HYPOXIA</a></td>
<td><a href='HALLMARK_HYPOXIA.html'>Details ...</a></td></tr>
</table></div></body></html>
"""

#: The MSigDB annotation index, which is an Apache directory listing.
CHIP_INDEX_HTML = """<html><body><h1>Index of /annotations_versioned</h1><pre>
<a href="?C=N;O=D">Name</a>
<a href="/gsea-msigdb/msigdb/">Parent Directory</a>
<a href="Human_AFFY_HG_U133.chip">Human_AFFY_HG_U133.chip</a>
<a href="Human_Ensembl_Gene_ID_MSigDB.v7.5.1.chip">Human_Ensembl_Gene_ID...</a>
<a href="Mouse_Gene_Symbol_Remapping.chip">Mouse_Gene_Symbol...</a>
<a href="Human_notes.txt">Human_notes.txt</a>
</pre></body></html>
"""

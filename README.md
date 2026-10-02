# gsea-pipeline

Prepare [GSEA](https://www.gsea-msigdb.org/gsea/) inputs from Proline proteomics
exports, drive the GSEA desktop command line tool, and read the reports it
produces.

The workflow it automates:

1. **prepare** — a Proline CSV export becomes the files GSEA wants: a `.gct`
   expression matrix, a `.cls` phenotype file, and a `.txt` matrix. Feature names
   can be reduced to gene symbols or mapped to KEGG gene identifiers through the
   UniProt ID mapping service.
2. **chips** — list and download the MSigDB `*.chip` platform annotations.
3. **run** — invoke `gsea-cli GSEA` once per phenotype comparison.
4. **report** — summarise each run (how many gene sets reached FDR < 25%) and
   export every gene set's enrichment table as CSV.

## Install

```bash
python -m pip install -e .            # requests is the only runtime dependency
python -m pip install -e '.[dev]'     # plus pytest
python -m pip install -e '.[excel]'   # plus openpyxl, needed only by `tally`
```

## Use

Put the raw exports in `data/raw/` and run:

```bash
gsea-pipeline prepare                      # -> data/gct, data/phenotypes, data/txt
gsea-pipeline prepare --naming kegg        # map accessions to KEGG gene numbers
gsea-pipeline prepare --format wide        # a pandas-readable CSV instead

gsea-pipeline chips                        # list the Human_*.chip annotations
gsea-pipeline chips --download             # -> data/chips

gsea-pipeline run \
    --res data/gct/skuska.gct \
    --cls data/phenotypes/skuska.cls \
    --gmx data/gmt/h.all.v7.5.1.symbols.gmt \
    --chip data/chips/Human_Gene_Symbol_with_Remapping_MSigDB.v7.5.1.chip \
    --set nperm=100 --dry-run             # drop --dry-run to run it

gsea-pipeline report                       # summarise every run under data/gsea
gsea-pipeline report --export              # also write the gene set tables as CSV

gsea-pipeline tally export1.xlsx export2.xlsx -o results.txt
```

`python -m gsea_pipeline` works the same way. `--help` on any subcommand lists
its options; `-v` logs every step, `-q` only problems.

### Configuration

| What | How |
| --- | --- |
| Data directory | `--data-dir`, else `$GSEA_DATA_DIR`, else `./data` |
| GSEA installation | `--gsea-home`, else `$GSEA_HOME`, else searched for |
| GSEA parameters | `--set FLAG=VALUE`, repeatable; defaults in `gsea.DEFAULT_PARAMETERS` |

`data/raw/` is the only part of `data/` under version control. Everything else in
it is regenerated from those tables, so it is ignored.

## Layout

```
src/gsea_pipeline/
  config.py        where files live
  naming.py        Proline column and UniProt name normalisation
  matrix.py        the expression matrix, and reading one from a delimited file
  phenotypes.py    sample groups and .cls files
  writers.py       rendering a matrix as GCT, TXT or CSV
  uniprot.py       accession -> KEGG gene mapping
  annotations.py   MSigDB *.chip listing and download
  gsea.py          locating and running GSEA desktop
  reports.py       reading the HTML GSEA writes
  htmlparse.py     the small HTML reader reports.py and annotations.py use
  proteins.py      protein tallies over Proline spreadsheet exports
  pipeline.py      raw table in, GSEA inputs out
  cli.py           the command line interface
```

## Develop

```bash
python -m pytest
```

178 tests, no network access and no GSEA installation required: the UniProt and
MSigDB clients take a `session`, and the GSEA runner takes a `runner`.

## What changed in the rewrite

This replaces seven flat scripts (`base.py`, `convert_file.py`,
`convert_proline_files.py`, `paths.py`, `id_mapping.py`, `scrape.py`, `scan.py`)
and a scratch notebook. The behaviour is the same except where it was wrong.

**Bugs fixed**

- `run_gsea` passed a list to `subprocess.run(..., shell=True)`. On POSIX that
  runs the first element and discards every argument after it, so GSEA ran with
  no parameters at all. The command is now a list with `shell=False`, and Windows
  `.bat` launchers go through `cmd /c`.
- `scrape_for_score` read the *first* `<li>` of `index.html` — the "upregulated
  in phenotype" count, not the FDR count its docstring described — and sliced it
  at fixed offsets, raising `ValueError` on the reports in this repository. Both
  phenotypes' counts are now matched by pattern.
- `scrape_file` wrote each table to `f'{file}'[:-4] + '.csv'`, cutting four
  characters off the *gene set name* rather than an extension; that is why the
  old output holds `HALLMARK_COAGULA.csv`. The full name is kept.
- `get_kegg_ids` returned an unbound local when the results were not ready.
- The UniProt polling loop raised on any status that was not exactly `RUNNING`,
  including the `NEW` a job is first queued as.
- No HTTP request had a timeout, so a stalled server hung the pipeline for good.
- `get_sample_code` scanned `string.lstrip()` but indexed into `string`, so a
  padded sample name such as `" P5"` split as `("", " P5")`.
- Fixed-width slices mis-named anything that deviated by a character:
  `name[:-6]` on a name with no `_HUMAN` suffix, `kegg[4:]` on an organism code
  that was not three letters, `split(' ')[-1][:-1]` on a header with no trailing
  parenthesis. These are patterns now, and total.
- Ragged input rows were silently written out misaligned; they are now rejected
  with the offending line number.
- Input was split on `,` and `;` by hand, so a quoted Proline description
  containing a comma broke the row. Parsing goes through `csv` both ways.
- Importing `paths.py` ran `os.scandir` and, with more than one GSEA install on
  Windows, blocked on an `input()` prompt. Nothing happens at import now.
- `run_gsea` and `download_files` used `os.chdir` and only changed back on
  success, leaving the process in the wrong directory after any failure. Both use
  `cwd=`.
- Remote filenames were interpolated into `os.system('wget ' + url + item)`.
  Downloads go through `requests`, and a filename that is not a plain basename is
  refused.

**Dependencies dropped**

`pandas`, `beautifulsoup4` and `xlrd` are gone; `requests` is all that is left.
The one pandas call is three lines of `csv`, BeautifulSoup is replaced by
`htmlparse.py` over the standard library's `html.parser`, and `xlrd` — which has
not read `.xlsx` since version 2.0 — became an optional `openpyxl` adapter used
only by `tally`.

**Structure**

- `convert_file.py` and `convert_proline_files.py` were the same pipeline twice
  over, differing only in a delimiter and in how features were named. Each
  re-read its input once per output format, and built its output with
  `text = text + line` — quadratic in the number of features. One parse now feeds
  every writer.
- Every entry point was a `__main__` block with the interesting choices commented
  out (which file, which gene set database, whether to download annotations).
  Those are flags.
- `scan.py` accumulated into a module level dict, so its statistics described
  whatever had been loaded last and could not be tested without an Excel file.

**Two cosmetic output differences**

- The wide CSV is written as `DataFrame.to_csv()` writes it, quoting only where a
  comma or quote requires it rather than quoting every header cell. It parses to
  exactly the same cells as the old output.
- Exported gene set tables keep the double quotes Ensembl puts around
  descriptions that contain commas, escaped per RFC 4180, instead of deleting
  every `"` from the data.

"""Name normalisation.

Proline exports carry decorated column headers and UniProt-style protein names;
GSEA wants short sample codes and gene symbols.  The old code did this with
fixed-width slices (``name.split(' ')[-1][:-1]``, ``ids[:-6]``, ``kegg[4:]``),
which silently produced wrong names as soon as a header or accession deviated by
one character.  The equivalents here are explicit and total.
"""

from __future__ import annotations

import re

#: Trailing parenthesised group of a Proline column header, e.g. ``norm(... Z1)``.
_TRAILING_PARENS = re.compile(r"\(([^()]*)\)\s*$")

#: A UniProt entry-name organism suffix, e.g. the ``_HUMAN`` of ``MYH9_HUMAN``.
_ORGANISM_SUFFIX = re.compile(r"_[A-Z][A-Z0-9]{2,}$")

#: Leading non-digits of a sample name, e.g. the ``Z`` of ``Z12``.
_SAMPLE_CODE = re.compile(r"^(?P<code>\D*)(?P<number>.*)$", re.DOTALL)


def sample_name(column: str) -> str:
    """Reduce a Proline column header to the bare sample name.

    The quantitation columns are named after the metric applied to the sample,
    with the sample itself last inside parentheses::

        >>> sample_name("norm(Weighted SC Z1)")
        'Z1'
        >>> sample_name(" C12 ")
        'C12'

    A header with no parentheses and no spaces is returned as-is, so already
    normalised tables survive a second pass unchanged.
    """
    text = column.strip()
    inner = _TRAILING_PARENS.search(text)
    if inner is not None:
        text = inner.group(1).strip()
    parts = text.split()
    return parts[-1] if parts else text


def strip_organism_suffix(name: str) -> str:
    """Drop the organism suffix from a UniProt entry name.

    ``MYH9_HUMAN`` becomes ``MYH9``.  Names without such a suffix -- a bare gene
    symbol, or a numeric KEGG identifier -- are left alone::

        >>> strip_organism_suffix("MYH9_HUMAN")
        'MYH9'
        >>> strip_organism_suffix("HLA_A")
        'HLA_A'
        >>> strip_organism_suffix("4627")
        '4627'
    """
    return _ORGANISM_SUFFIX.sub("", name.strip())


def strip_kegg_organism(kegg_id: str) -> str:
    """Return the gene part of a KEGG identifier: ``hsa:4627`` -> ``4627``."""
    return kegg_id.strip().rpartition(":")[2]


def split_sample_code(sample: str) -> tuple[str, str]:
    """Split a sample name into its group code and its number.

    Sample names are a group prefix followed by a replicate number, so the
    prefix is what the phenotype file groups on::

        >>> split_sample_code("Z12")
        ('Z', '12')
        >>> split_sample_code(" P5 ")
        ('P', '5')
        >>> split_sample_code("control")
        ('control', '')
    """
    match = _SAMPLE_CODE.match(sample.strip())
    assert match is not None  # the pattern matches any string
    return match.group("code"), match.group("number")


def sample_group(sample: str) -> str:
    """Return just the group code of a sample name."""
    return split_sample_code(sample)[0]

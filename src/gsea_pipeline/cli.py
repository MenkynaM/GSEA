"""Command line interface.

Every entry point the old scripts had was a ``__main__`` block with the
interesting arguments commented out -- which file to analyse, which gene set
database, whether to download the annotations.  They are flags here.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .annotations import CHIP_INDEX_URL, download_chip_files, list_chip_files
from .config import DataLayout
from .errors import GseaPipelineError
from .gsea import GSEA_HOME_ENV, GseaInstallation, run_gsea
from .phenotypes import read_cls
from .pipeline import DEFAULT_FORMATS, FeatureNaming, OutputFormat, prepare_all
from .proteins import DEFAULT_COUNT_COLUMN, DEFAULT_NAME_COLUMN, tally_spreadsheets
from .reports import export_gene_set_tables, find_reports, summarise_index

LOGGER = logging.getLogger("gsea_pipeline")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gsea-pipeline",
        description="Prepare GSEA inputs, run GSEA, and read its reports.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="root of the data tree (default: $GSEA_DATA_DIR, else ./data)",
    )
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v", "--verbose", action="store_true", help="log every step in detail"
    )
    verbosity.add_argument(
        "-q", "--quiet", action="store_true", help="log warnings and errors only"
    )

    subcommands = parser.add_subparsers(dest="command", required=True)
    _add_prepare(subcommands)
    _add_run(subcommands)
    _add_chips(subcommands)
    _add_report(subcommands)
    _add_tally(subcommands)
    return parser


def _add_prepare(subcommands) -> None:
    prepare = subcommands.add_parser(
        "prepare", help="convert raw tables into GSEA inputs (.gct, .cls, .txt)"
    )
    prepare.add_argument(
        "sources",
        nargs="*",
        type=Path,
        help="raw tables to convert (default: every file in <data-dir>/raw)",
    )
    prepare.add_argument(
        "--naming",
        type=FeatureNaming,
        choices=list(FeatureNaming),
        default=FeatureNaming.SYMBOL,
        help="how to name features: strip the organism suffix, map to KEGG, or leave as-is",
    )
    prepare.add_argument(
        "--format",
        dest="formats",
        type=OutputFormat,
        choices=list(OutputFormat),
        action="append",
        help="an output to write; repeatable (default: gct, cls and txt)",
    )
    prepare.add_argument(
        "--delimiter",
        default=None,
        help="input delimiter (default: detected from the header line)",
    )
    prepare.set_defaults(handler=_do_prepare)


def _add_run(subcommands) -> None:
    run = subcommands.add_parser("run", help="run GSEA over the prepared inputs")
    run.add_argument("--res", type=Path, required=True, help="expression matrix (.gct)")
    run.add_argument("--cls", type=Path, required=True, help="phenotype file (.cls)")
    run.add_argument(
        "--comparison",
        default=None,
        help="phenotype comparison, e.g. P_versus_K (default: every comparison in the .cls)",
    )
    run.add_argument("--gmx", type=Path, required=True, help="gene set database (.gmt)")
    run.add_argument("--chip", type=Path, required=True, help="platform annotation (.chip)")
    run.add_argument("--out", type=Path, default=None, help="where GSEA writes its report")
    run.add_argument(
        "--gsea-home", type=Path, default=None, help=f"GSEA install (default: ${GSEA_HOME_ENV})"
    )
    run.add_argument(
        "--set",
        dest="parameters",
        action="append",
        default=[],
        metavar="FLAG=VALUE",
        help=(
            "override a GSEA parameter, e.g. --set nperm=100; the leading dash is "
            "optional because argparse would read it as an option of its own; repeatable"
        ),
    )
    run.add_argument(
        "--dry-run", action="store_true", help="print the command without running it"
    )
    run.set_defaults(handler=_do_run)


def _add_chips(subcommands) -> None:
    chips = subcommands.add_parser("chips", help="list or download MSigDB .chip annotations")
    chips.add_argument(
        "--download", action="store_true", help="download the listed files instead of printing them"
    )
    chips.add_argument("--prefix", default="Human_", help="filename prefix to keep")
    chips.add_argument("--index-url", default=CHIP_INDEX_URL, help="MSigDB annotation index")
    chips.add_argument("--overwrite", action="store_true", help="re-download existing files")
    chips.set_defaults(handler=_do_chips)


def _add_report(subcommands) -> None:
    report = subcommands.add_parser("report", help="summarise or export GSEA reports")
    report.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="report directories (default: every one under <data-dir>/gsea)",
    )
    report.add_argument(
        "--export",
        action="store_true",
        help="also write each gene set's enrichment table as CSV",
    )
    report.set_defaults(handler=_do_report)


def _add_tally(subcommands) -> None:
    tally = subcommands.add_parser(
        "tally", help="aggregate protein counts across Proline spreadsheet exports"
    )
    tally.add_argument("sources", nargs="+", type=Path, help="spreadsheet files to read")
    tally.add_argument(
        "--name-column", type=int, default=DEFAULT_NAME_COLUMN, help="0-based protein name column"
    )
    tally.add_argument(
        "--count-column", type=int, default=DEFAULT_COUNT_COLUMN, help="0-based count column"
    )
    tally.add_argument(
        "-o", "--output", type=Path, default=None, help="write the report here instead of stdout"
    )
    tally.set_defaults(handler=_do_tally)


# -- handlers ------------------------------------------------------------


def _do_prepare(args: argparse.Namespace, layout: DataLayout) -> int:
    prepared = prepare_all(
        layout,
        sources=args.sources or None,
        naming=args.naming,
        formats=args.formats or DEFAULT_FORMATS,
        delimiter=args.delimiter,
    )
    for item in prepared:
        print(
            f"{item.source.name}: {item.matrix.n_features} features, "
            f"{item.matrix.n_samples} samples, "
            f"phenotypes {'/'.join(item.phenotypes.classes)}"
        )
        for fmt, path in item.outputs.items():
            print(f"  {fmt.value:>6}  {path}")
    return 0 if prepared else 1


def _parse_overrides(pairs: Sequence[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for pair in pairs:
        flag, separator, value = pair.partition("=")
        if not separator:
            raise GseaPipelineError(f"--set expects FLAG=VALUE, got {pair!r}")
        overrides[flag if flag.startswith("-") else f"-{flag}"] = value
    return overrides


def _do_run(args: argparse.Namespace, layout: DataLayout) -> int:
    installation = GseaInstallation.discover(args.gsea_home)
    out = args.out or layout.gsea_output
    parameters = _parse_overrides(args.parameters)

    comparisons = (
        [args.comparison] if args.comparison else read_cls(args.cls).comparisons(include_rest=False)
    )
    for comparison in comparisons:
        command = run_gsea(
            installation,
            res=args.res,
            cls=f"{args.cls}#{comparison}",
            gmx=args.gmx,
            chip=args.chip,
            out=out,
            parameters=parameters,
            dry_run=args.dry_run,
        )
        if args.dry_run:
            print(" ".join(command))
    return 0


def _do_chips(args: argparse.Namespace, layout: DataLayout) -> int:
    names = list_chip_files(index_url=args.index_url, prefix=args.prefix)
    if not names:
        LOGGER.warning("no files matching %r at %s", args.prefix, args.index_url)
        return 1
    if not args.download:
        print("\n".join(names))
        return 0
    paths = download_chip_files(
        names, layout.chips, index_url=args.index_url, overwrite=args.overwrite
    )
    print(f"{len(paths)} annotation files in {layout.chips}")
    return 0


def _do_report(args: argparse.Namespace, layout: DataLayout) -> int:
    directories = [p for p in args.paths] or find_reports(layout.gsea_output)
    if not directories:
        LOGGER.warning("no GSEA reports found under %s", layout.gsea_output)
        return 1

    for directory in directories:
        summary = summarise_index(directory / "index.html")
        print(f"{directory.name}: {summary.score} gene sets at FDR < 25%")
        for phenotype in summary.phenotypes:
            print(
                f"  {phenotype.phenotype}: {phenotype.upregulated}/{phenotype.gene_sets} "
                f"upregulated, {phenotype.fdr_below_25} at FDR < 25%, "
                f"{phenotype.nominal_p_below_5} at p < 5%"
            )
        if args.export:
            written = export_gene_set_tables(directory)
            print(f"  exported {len(written)} gene set tables")
    return 0


def _do_tally(args: argparse.Namespace, layout: DataLayout) -> int:
    counts = tally_spreadsheets(
        args.sources, name_column=args.name_column, count_column=args.count_column
    )
    report = counts.render_report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf8")
        print(f"{len(counts)} proteins written to {args.output}")
    else:
        sys.stdout.write(report)
    return 0


def _configure_logging(level: int) -> None:
    """Send this package's log records to stderr at ``level``.

    The level goes on the package logger rather than the root one: a bare
    ``basicConfig`` is a no-op when the host already installed a handler, which
    silently swallowed ``-v``.
    """
    logging.basicConfig(format="%(levelname)s %(message)s")
    LOGGER.setLevel(level)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit status."""
    args = build_parser().parse_args(argv)
    _configure_logging(
        logging.DEBUG if args.verbose else logging.WARNING if args.quiet else logging.INFO
    )
    layout = DataLayout.from_env(args.data_dir)
    try:
        return args.handler(args, layout)
    except GseaPipelineError as exc:
        # Straight to stderr rather than through the logger: an expected failure
        # is part of this program's output, not of its diagnostics.
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover - interactive only
        print("interrupted", file=sys.stderr)
        return 130

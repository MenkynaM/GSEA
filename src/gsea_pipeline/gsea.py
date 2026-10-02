"""Finding the GSEA desktop installation and running its command line tool.

Three things changed from the original ``base.py``:

* Locating the installation no longer prompts during import.  It is a function,
  it checks ``$GSEA_HOME`` first, and when several installations are present it
  picks the highest version and says so instead of asking at a prompt.
* The command is run with ``cwd=`` instead of ``os.chdir()``, which left the
  process in the GSEA directory whenever the run raised.
* ``shell=True`` is gone.  Passing a *list* with ``shell=True`` makes POSIX
  execute the first element and discard every argument after it, so the original
  ran GSEA with no parameters at all on Linux.  Windows ``.bat`` launchers still
  need an interpreter, so those are run through ``cmd /c`` explicitly.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .errors import GseaNotFoundError

LOGGER = logging.getLogger(__name__)

#: Environment variable pointing at the GSEA installation directory.
GSEA_HOME_ENV = "GSEA_HOME"

#: Parameters sent with every run; override individually via ``parameters=``.
DEFAULT_PARAMETERS: Mapping[str, str] = {
    "-zip_report": "false",
    "-num": "100",
    "-scoring_scheme": "weighted",
    "-norm": "meandiv",
    "-mode": "Max_probe",
    "-include_only_symbols": "true",
    "-set_max": "500",
    "-set_min": "10",
    "-plot_top_x": "50",
    "-nperm": "1000",
    "-order": "descending",
    "-rnd_seed": "timestamp",
    "-rpt_label": "my_analysis",
    "-create_svgs": "false",
    "-sort": "real",
    "-create_gcts": "false",
    "-save_rnd_lists": "false",
    "-median": "false",
    "-metric": "Signal2Noise",
    "-make_sets": "true",
    "-rnd_type": "no_balance",
    "-permute": "phenotype",
    "-collapse": "Collapse",
}

_VERSION = re.compile(r"(\d+(?:\.\d+)*)")


def _version_key(path: Path) -> tuple:
    """Sort key ordering ``GSEA_4.2.3`` after ``GSEA_4.10`` by numeric parts."""
    match = _VERSION.search(path.name)
    if not match:
        return ((), path.name)
    return (tuple(int(part) for part in match.group(1).split(".")), path.name)


def candidate_homes() -> list[Path]:
    """Directories that look like a GSEA installation, on this platform."""
    roots: list[Path] = []
    if os.name == "nt":
        for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
            value = os.environ.get(env)
            if value:
                roots.append(Path(value))
    else:
        roots += [Path.cwd().parent, Path.home(), Path("/opt"), Path("/usr/local")]

    found: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            entries = sorted(root.iterdir())
        except OSError:  # unreadable directory on the search path
            continue
        found += [p for p in entries if p.is_dir() and p.name.upper().startswith("GSEA")]
    return sorted(dict.fromkeys(found), key=_version_key, reverse=True)


@dataclass(frozen=True)
class GseaInstallation:
    """A GSEA desktop installation and its command line launcher."""

    home: Path

    @property
    def launcher(self) -> Path:
        """The ``gsea-cli`` script shipped with this installation."""
        name = "gsea-cli.bat" if os.name == "nt" else "gsea-cli.sh"
        return self.home / name

    @classmethod
    def discover(cls, home: str | os.PathLike[str] | None = None) -> GseaInstallation:
        """Locate an installation: the argument, ``$GSEA_HOME``, then the defaults."""
        explicit = home or os.environ.get(GSEA_HOME_ENV)
        if explicit:
            installation = cls(Path(explicit).expanduser().resolve())
            if not installation.launcher.exists():
                raise GseaNotFoundError(
                    f"{installation.home} contains no {installation.launcher.name}"
                )
            return installation

        candidates = [c for c in candidate_homes() if cls(c).launcher.exists()]
        if not candidates:
            raise GseaNotFoundError(
                "no GSEA installation found; download GSEA desktop from "
                f"https://www.gsea-msigdb.org/gsea/ and set ${GSEA_HOME_ENV} to it"
            )
        if len(candidates) > 1:
            LOGGER.warning(
                "several GSEA installations found (%s); using %s -- set $%s to choose",
                ", ".join(c.name for c in candidates),
                candidates[0].name,
                GSEA_HOME_ENV,
            )
        return cls(candidates[0])


def build_command(
    installation: GseaInstallation,
    *,
    res: Path,
    cls: str,
    gmx: Path,
    chip: Path,
    out: Path,
    parameters: Mapping[str, str] | None = None,
) -> list[str]:
    """Build the ``gsea-cli GSEA ...`` argument list.

    ``cls`` is a path with the comparison appended, as GSEA expects it:
    ``phenotypes/skuska.cls#P_versus_K``.
    """
    settings = dict(DEFAULT_PARAMETERS)
    if parameters:
        settings.update(parameters)
    settings["-out"] = str(out)

    command = [str(installation.launcher), "GSEA"]
    if os.name == "nt":
        command = ["cmd", "/c", *command]
    for flag, value in settings.items():
        command += [flag, str(value)]
    command += ["-res", str(res), "-cls", str(cls)]
    command += ["-gmx", str(gmx), "-chip", str(chip)]
    return command


def run_gsea(
    installation: GseaInstallation,
    *,
    res: Path,
    cls: str,
    gmx: Path,
    chip: Path,
    out: Path,
    parameters: Mapping[str, str] | None = None,
    dry_run: bool = False,
    runner=subprocess.run,
) -> Sequence[str]:
    """Run one GSEA analysis and return the command that was used.

    With ``dry_run`` the command is logged and not executed, which is how the CLI
    lets a caller check a parameter sweep before committing to it.
    """
    out.mkdir(parents=True, exist_ok=True)
    command = build_command(
        installation, res=res, cls=cls, gmx=gmx, chip=chip, out=out, parameters=parameters
    )
    LOGGER.info("running: %s", " ".join(command))
    if not dry_run:
        runner(command, cwd=installation.home, check=True)
    return command

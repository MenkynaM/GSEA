"""Exception hierarchy for the package.

Every failure mode the package raises on purpose derives from
:class:`GseaPipelineError`, so a caller (the CLI included) can distinguish an
expected, explainable problem from a genuine bug.
"""

from __future__ import annotations


class GseaPipelineError(Exception):
    """Base class for every error raised deliberately by this package."""


class ConfigurationError(GseaPipelineError):
    """Something about the environment or the given paths is unusable."""


class GseaNotFoundError(ConfigurationError):
    """No GSEA desktop installation could be located."""


class MalformedTableError(GseaPipelineError):
    """An input table does not have the structure this package expects."""

    def __init__(self, path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        super().__init__(f"{path}:{line}: {message}")


class ReportParsingError(GseaPipelineError):
    """A GSEA HTML report did not contain the data we went looking for."""


class RemoteServiceError(GseaPipelineError):
    """A remote service (UniProt, MSigDB) behaved unexpectedly."""

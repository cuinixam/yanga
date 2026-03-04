from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ArtifactPredicate = Callable[["Artifact"], bool]


@dataclass
class Artifact:
    path: Path  # file or directory
    provider: str  # step or component that produced this
    consumers: list[str] | None = None  # None = global; named list = restricted
    labels: list[str] | None = None  # well-known: "include", "public", "private", "source"


def with_label(label: str) -> ArtifactPredicate:
    return lambda artifact: label in (artifact.labels or [])


def for_consumer(consumer: str | None = None) -> ArtifactPredicate:
    """
    Filter artifacts based on their consumers.

    consumer=None  → global artifacts only (artifact.consumers is None)
    consumer="X"   → global + artifacts explicitly targeting "X"
    """
    return lambda artifact: artifact.consumers is None or (consumer is not None and consumer in artifact.consumers)


def filter_artifacts(
    artifacts: list[Artifact],
    *predicates: ArtifactPredicate,
) -> list[Artifact]:
    return [a for a in artifacts if all(p(a) for p in predicates)]


def collect_directories(artifacts: list[Artifact]) -> list[Path]:
    """Extract unique directory paths from artifacts. File paths are resolved to their parent."""
    return list(dict.fromkeys(a.path if a.path.is_dir() else a.path.parent for a in artifacts))

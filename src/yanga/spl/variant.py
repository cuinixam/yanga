from dataclasses import dataclass, field
from typing import List, Optional

from mashumaro.mixins.yaml import DataClassYAMLMixin


@dataclass
class VariantConfig(DataClassYAMLMixin):
    """
    .. item:: IMPL-VariantConfig
        :fulfills:
            REQ-VARIANT_NAME-0.0.1
            REQ-VARIANT_SLUG-0.0.1
            REQ-VARIANT_DESCRIPTION-0.0.1
            REQ-VARIANT_TAGS-0.0.1
    """

    name: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    _slug: Optional[str] = None

    def generate_slug(self, slug: Optional[str] = None) -> str:
        return (slug or self.name).lower().replace(" ", "-")

    @property
    def slug(self) -> str:
        return self._slug or self.generate_slug()

    @slug.setter
    def slug(self, slug: str) -> None:
        self._slug = self.generate_slug(slug)

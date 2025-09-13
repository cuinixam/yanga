from pathlib import Path

from kspl.config_slurper import KConfigData, VariantData, VariantViewData
from kspl.gui import KSPL
from kspl.kconfig import EditableConfigElement, KConfig
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger
from py_app_dev.mvp.event_manager import EventManager

from yanga.domain.project_slurper import YangaProjectSlurper
from yanga.gui.icons import Icons


class YangaKConfigData(KConfigData):
    """Yanga implementation of KConfigData protocol for viewing feature configurations."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir.absolute()
        self.project_slurper = YangaProjectSlurper(project_dir)
        self.logger = logger.bind()

        # Load KConfig model if it exists
        self.kconfig_model_file = self.project_dir / "KConfig"
        if not self.kconfig_model_file.is_file():
            raise UserNotificationException(f"KConfig file not found at {self.kconfig_model_file}")

        self.base_kconfig = KConfig(self.kconfig_model_file)
        self.variant_kconfigs: list[VariantData] = []
        self._load_variant_configs()

    def _load_variant_configs(self) -> None:
        """Load KConfig configurations for all variants."""
        self.variant_kconfigs = []

        for variant_config in self.project_slurper.variants:
            if variant_config.features_selection_file:
                # Get the features selection file path
                features_file = self.project_slurper.get_variant_config_file(variant_config.name)
                if features_file and features_file.exists():
                    kconfig = KConfig(self.kconfig_model_file, features_file)
                    self.variant_kconfigs.append(VariantData(variant_config.name, kconfig))
                else:
                    self.logger.warning(f"Features selection file not found for variant {variant_config.name}: {variant_config.features_selection_file}")
                    # Use base configuration without selection file
                    kconfig = KConfig(self.kconfig_model_file)
                    self.variant_kconfigs.append(VariantData(variant_config.name, kconfig))
            else:
                # Use base configuration for variants without features selection
                kconfig = KConfig(self.kconfig_model_file)
                self.variant_kconfigs.append(VariantData(variant_config.name, kconfig))

        # If no variants found, create a default one
        if not self.variant_kconfigs:
            self.variant_kconfigs.append(VariantData("Default", self.base_kconfig))

    def get_elements(self) -> list[EditableConfigElement]:
        """Get all configuration elements from the base KConfig model."""
        return self.base_kconfig.elements

    def get_variants(self) -> list[VariantViewData]:
        """Get variant view data for all loaded variants."""
        variants = []
        for variant in self.variant_kconfigs:
            config_dict = {config_elem.name: config_elem.value for config_elem in variant.config.elements if not config_elem.is_menu}
            variants.append(VariantViewData(variant.name, config_dict))
        return variants

    def find_variant_config(self, variant_name: str) -> VariantData | None:
        """Find variant configuration by name."""
        for variant in self.variant_kconfigs:
            if variant.name == variant_name:
                return variant
        return None

    def refresh_data(self) -> None:
        """Refresh the configuration data by reloading everything."""
        self.logger.info("Refreshing Yanga KConfig data...")

        # Reload project configuration
        self.project_slurper = YangaProjectSlurper(self.project_dir)

        # Reload KConfig model
        self.base_kconfig = KConfig(self.kconfig_model_file)

        # Reload variant configurations
        self._load_variant_configs()

        self.logger.info(f"Refreshed data: found {len(self.variant_kconfigs)} variants")


class KConfigView:
    """View for displaying the KConfig data for all variants."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.logger = logger.bind()

    def run(self) -> None:
        """Run the KConfig viewer GUI."""
        try:
            event_manager = EventManager()
            kconfig_data: KConfigData = YangaKConfigData(self.project_dir)
            KSPL(event_manager, kconfig_data, icon_file=Icons.YANGA_ICON.file).run()
        except UserNotificationException as e:
            self.logger.error(f"Failed to start KConfig viewer: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error starting KConfig viewer: {e}")
            raise

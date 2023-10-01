from enum import auto
from pathlib import Path
from typing import List, Optional

import customtkinter
from py_app_dev.core.exceptions import UserNotificationException
from py_app_dev.core.logging import logger, time_it
from py_app_dev.mvp.event_manager import EventID, EventManager
from py_app_dev.mvp.presenter import Presenter
from py_app_dev.mvp.view import View

from yanga.project.project import YangaProject
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import StageRunner


class YangaEvent(EventID):
    BUILD_EVENT = auto()
    REFRESH_EVENT = auto()


class YangaView(View):
    def __init__(self, event_manager: EventManager) -> None:
        self.event_manager = event_manager
        self.root = customtkinter.CTk()
        self.variants: List[str] = []

    def init_gui(self) -> None:
        customtkinter.set_default_color_theme("green")

        # Configure the main window
        self.root.title("YANGA")
        self.root.geometry(f"{220}x{200}")

        # Create selection list
        self.variant_selection = customtkinter.CTkOptionMenu(self.root)
        self.variant_selection.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._update_variants(self.variant_selection, self.variants)

        # Create the build button
        self.build_button = customtkinter.CTkButton(
            self.root, text="Build", command=self._build_button_pressed
        )
        self.build_button.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # Create the refresh button
        self.refresh_button = customtkinter.CTkButton(
            self.root, text="Refresh", command=self._refresh_button_pressed
        )
        self.refresh_button.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # Create events
        self.build_trigger = self.event_manager.create_event_trigger(
            YangaEvent.BUILD_EVENT
        )
        self.refresh_trigger = self.event_manager.create_event_trigger(
            YangaEvent.REFRESH_EVENT
        )

    def _build_button_pressed(self) -> None:
        self.build_trigger(self.variant_selection.get())

    def _refresh_button_pressed(self) -> None:
        self.refresh_trigger()

    def mainloop(self) -> None:
        self.root.mainloop()

    @staticmethod
    def _update_variants(
        variant_selection: customtkinter.CTkOptionMenu, variants: List[str]
    ) -> None:
        if variants:
            variant_selection.configure(values=variants)
            variant_selection.set(variants[0])
        else:
            variant_selection.configure(values=["No variants found"])
            variant_selection.set("No variants found")

    def update_variants(self, variants: List[str]) -> None:
        self.variants = variants
        self.variants.sort()
        # sort variants alphabetically
        self._update_variants(self.variant_selection, variants)


class YangaPresenter(Presenter):
    def __init__(
        self, view: YangaView, event_manager: EventManager, project_dir: Path
    ) -> None:
        self.logger = logger.bind()
        self.view = view
        self.event_manager = event_manager
        self.project_dir = project_dir
        self.project = self._create_project()
        self.event_manager.subscribe(YangaEvent.BUILD_EVENT, self._build_trigger)
        self.event_manager.subscribe(YangaEvent.REFRESH_EVENT, self._refresh_trigger)
        self.build_running_flag = False

    def run(self) -> None:
        self.view.init_gui()
        self.view.update_variants(self._create_variant_names())
        self.view.mainloop()

    def _build_trigger(self, variant_name: str) -> None:
        if self.build_running_flag:
            self.logger.warning("Build already running")
            return
        self.run_build(variant_name)

    def _refresh_trigger(self) -> None:
        self.project = self._create_project()
        self.view.update_variants(self._create_variant_names())

    @time_it()
    def run_build(self, variant_name: str) -> None:
        if not self.project:
            self.logger.warning("Project is not loaded")
            return
        self.logger.info(f"Build trigger for variant {variant_name}")
        self.build_running_flag = True
        build_environment = BuildEnvironment(
            variant_name, self.project_dir, self.project.components
        )
        for stage in self.project.stages:
            StageRunner(build_environment, stage).run()
        self.build_running_flag = False

    def _create_project(self) -> Optional[YangaProject]:
        try:
            return YangaProject(self.project_dir)
        except UserNotificationException as e:
            self.logger.error(e)
            return None

    def _create_variant_names(self) -> List[str]:
        if self.project:
            return [variant.name for variant in self.project.variants]
        return []


class YangaGui:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.logger = logger.bind()

    def run(self) -> None:
        try:
            event_manager = EventManager()
            view = YangaView(event_manager)
            presenter = YangaPresenter(view, event_manager, self.project_dir)
            presenter.run()
        except UserNotificationException as e:
            self.logger.error(e)

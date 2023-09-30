from enum import auto
from pathlib import Path
from typing import List

import customtkinter
from py_app_dev.core.logging import logger, time_it
from py_app_dev.mvp.event_manager import EventID, EventManager
from py_app_dev.mvp.presenter import Presenter
from py_app_dev.mvp.view import View

from yanga.project.project import YangaProject
from yanga.ybuild.environment import BuildEnvironment
from yanga.ybuild.pipeline import StageRunner


class YangaEvent(EventID):
    BUILD_TRIGGER = auto()


class YangaView(View):
    def __init__(self, event_manager: EventManager) -> None:
        self.event_manager = event_manager
        self.root = customtkinter.CTk()
        self.variants: List[str] = []

    def init_gui(self) -> None:
        # Configure the main window
        self.root.title("YANGA")
        self.root.geometry(f"{800}x{600}")

        # Create selection list
        self.variant_selection = customtkinter.CTkOptionMenu(self.root)
        self.variant_selection.grid(row=0, column=0, sticky="nsew")
        self._update_variants(self.variant_selection, self.variants)

        # Create the build button
        self.build_button = customtkinter.CTkButton(
            self.root, text="Build", command=self._build_button_pressed
        )
        self.build_button.grid(row=0, column=1, sticky="nsew")

        # Create events
        self.build_trigger = self.event_manager.create_event_trigger(
            YangaEvent.BUILD_TRIGGER
        )

    def _build_button_pressed(self) -> None:
        self.build_trigger(self.variant_selection.get())

    def mainloop(self) -> None:
        self.root.mainloop()

    @staticmethod
    def _update_variants(
        variant_selection: customtkinter.CTkOptionMenu, variants: List[str]
    ) -> None:
        if variants:
            variant_selection.configure(values=variants)
            variant_selection.set(variants[0])

    def update_variants(self, variants: List[str]) -> None:
        self.variants = variants
        self.variants.sort()
        # sort variants alphabetically
        self._update_variants(self.variant_selection, variants)


class YangaPresenter(Presenter):
    def __init__(
        self, view: YangaView, event_manager: EventManager, project_dir: Path
    ) -> None:
        self.view = view
        self.event_manager = event_manager
        self.project_dir = project_dir
        self.project = YangaProject(self.project_dir)
        self.event_manager.subscribe(YangaEvent.BUILD_TRIGGER, self._build_trigger)
        self.logger = logger.bind()
        self.build_running_flag = False

    def run(self) -> None:
        self.view.init_gui()
        self.view.update_variants([variant.name for variant in self.project.variants])
        self.view.mainloop()

    def _build_trigger(self, variant_name: str) -> None:
        if self.build_running_flag:
            self.logger.warning("Build already running")
            return
        self.run_build(variant_name)

    @time_it()
    def run_build(self, variant_name: str) -> None:
        self.logger.info(f"Build trigger for variant {variant_name}")
        self.build_running_flag = True
        build_environment = BuildEnvironment(
            variant_name, self.project_dir, self.project.components
        )
        for stage in self.project.stages:
            StageRunner(build_environment, stage).run()
        self.build_running_flag = False


class YangaGui:
    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir

    def run(self) -> None:
        event_manager = EventManager()
        view = YangaView(event_manager)
        presenter = YangaPresenter(view, event_manager, self.project_dir)
        presenter.run()

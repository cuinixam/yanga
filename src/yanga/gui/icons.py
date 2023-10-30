from enum import Enum
from pathlib import Path

import customtkinter
from PIL import Image


class Icons(Enum):
    YANGA_ICON = "yanga.ico"

    def __init__(self, file_name: str) -> None:
        self.resources_dir = Path(__file__).parent.joinpath("resources")
        self.file = self.resources_dir.joinpath(file_name).as_posix()

    @property
    def image(self) -> customtkinter.CTkImage:
        return customtkinter.CTkImage(
            dark_image=Image.open(self.file),
            size=(30, 30),
        )

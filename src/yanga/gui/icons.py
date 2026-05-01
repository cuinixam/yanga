from enum import Enum
from pathlib import Path

import customtkinter
from PIL import Image, ImageTk


class Icons(Enum):
    YANGA_ICON = "yanga.ico"
    YANGA_PNG = "yanga.png"

    def __init__(self, file_name: str) -> None:
        self.resources_dir = Path(__file__).parent.joinpath("resources")
        self.file = self.resources_dir.joinpath(file_name).as_posix()

    @property
    def image(self) -> customtkinter.CTkImage:
        return customtkinter.CTkImage(
            dark_image=Image.open(self.file),
            size=(30, 30),
        )

    @property
    def tk_photo(self) -> ImageTk.PhotoImage:
        # Tk's `iconphoto` needs a PhotoImage; `iconbitmap` is silently
        # ignored on macOS, so the window-icon path goes through this.
        return ImageTk.PhotoImage(Image.open(self.file))

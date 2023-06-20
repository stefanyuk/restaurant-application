import base64
import os
import secrets
from enum import Enum
from typing import Protocol

from src.settings import Settings


class PictureFormat(Enum):
    JPEG = "jpeg"
    PNG = "png"


class PictureSaver(Protocol):
    """Interface for saving pictures."""

    def save_picture(self, picture_data: str, picture_format: PictureFormat) -> str:
        """Save the picture.

        Args:
            picture_data (str): Base64 encoded string of the picture.
            picture_format (PictureFormat): format of the picture

        Returns:
            str: URL or path of the saved picture.
        """
        ...


class ServerPictureSaver:
    """Class implementing PictureSaver interface.

    It saves pictures on the server in the static folder.
    """

    _pictures_folder_name = "pictures"

    def __init__(self, app_settings: Settings) -> None:
        self.settings = app_settings

    def save_picture(self, picture_data: str, picture_format: PictureFormat) -> str:
        """Save the picture on the server.

        Args:
            picture_data (str): Base64 encoded string of the picture.
            picture_format (PictureFormat): format of the picture


        Returns:
            str: URL or path of the saved picture.
        """
        pictures_dir = self._create_pictures_dir_if_not_exists()
        new_picture_name = self._create_picture_name(picture_format)
        picture_data_decoded = base64.b64decode(picture_data)

        picture_path = os.path.join(pictures_dir, new_picture_name)
        with open(picture_path, "wb") as file:
            file.write(picture_data_decoded)

        return os.path.join(
            self.settings.static_folder_path,
            self._pictures_folder_name,
            new_picture_name,
        )

    def _create_picture_name(self, picture_format: PictureFormat):
        random_hex = secrets.token_hex(8)
        return random_hex + "." + picture_format.value

    def _create_pictures_dir_if_not_exists(self):
        pictures_dir = os.path.join(
            self.settings.static_folder_path, self._pictures_folder_name
        )

        if not os.path.exists(pictures_dir):
            os.makedirs(pictures_dir)

        return pictures_dir

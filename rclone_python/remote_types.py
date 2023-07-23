from enum import Enum


class RemoteTypes(Enum):
    """These are all the cloud systems support by rclone (generated with v1.63.1).
    A more detailed overview can be found here: https://rclone.org/overview/
    """

    amazon_cloud_drive = "amazon cloud drive"
    azureblob = "azureblob"
    b2 = "b2"
    box = "box"
    crypt = "crypt"
    cache = "cache"
    chunker = "chunker"
    combine = "combine"
    compress = "compress"
    drive = "drive"
    dropbox = "dropbox"
    fichier = "fichier"
    filefabric = "filefabric"
    ftp = "ftp"
    google_cloud_storage = "google cloud storage"

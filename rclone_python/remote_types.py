from enum import Enum


class RemoteTypes(Enum):
    """These are all the cloud systems support by rclone (generated with v1.63.1).
    A more detailed overview can be found here: https://rclone.org/overview/
    """

    combine = "combine"
    compress = "compress"
    drive = "drive"
    dropbox = "dropbox"
    fichier = "fichier"
    filefabric = "filefabric"
    ftp = "ftp"
    google_cloud_storage = "google cloud storage"

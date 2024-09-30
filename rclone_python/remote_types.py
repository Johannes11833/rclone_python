from enum import Enum


class RemoteTypes(Enum):
    """These are all the cloud systems support by rclone (generated with v1.68.1).
    A more detailed overview can be found here: https://rclone.org/overview/
    """

    azureblob = "azureblob"
    azurefiles = "azurefiles"
    b2 = "b2"
    box = "box"
    cache = "cache"
    chunker = "chunker"
    combine = "combine"
    compress = "compress"
    crypt = "crypt"
    drive = "drive"
    dropbox = "dropbox"
    fichier = "fichier"
    filefabric = "filefabric"
    filescom = "filescom"
    ftp = "ftp"
    gofile = "gofile"
    google_cloud_storage = "google cloud storage"
    google_photos = "google photos"
    hasher = "hasher"
    hdfs = "hdfs"
    hidrive = "hidrive"
    http = "http"
    imagekit = "imagekit"
    internetarchive = "internetarchive"
    jottacloud = "jottacloud"
    koofr = "koofr"
    linkbox = "linkbox"
    local = "local"
    mailru = "mailru"
    mega = "mega"
    memory = "memory"
    netstorage = "netstorage"
    onedrive = "onedrive"
    opendrive = "opendrive"
    oracleobjectstorage = "oracleobjectstorage"
    pcloud = "pcloud"
    pikpak = "pikpak"
    pixeldrain = "pixeldrain"
    premiumizeme = "premiumizeme"
    protondrive = "protondrive"
    putio = "putio"
    qingstor = "qingstor"
    quatrix = "quatrix"
    s3 = "s3"
    seafile = "seafile"
    sftp = "sftp"
    sharefile = "sharefile"
    sia = "sia"
    smb = "smb"
    storj = "storj"
    sugarsync = "sugarsync"
    swift = "swift"
    tardigrade = "tardigrade"
    ulozto = "ulozto"
    union = "union"
    uptobox = "uptobox"
    webdav = "webdav"
    yandex = "yandex"
    zoho = "zoho"

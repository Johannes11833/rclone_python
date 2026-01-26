import pytest
import platform
import zipfile
import tarfile
import urllib.request
import os
from unittest.mock import patch, MagicMock
from rclone_python import rclone, utils


@pytest.fixture(scope="module")
def CUSTOM_PATH(tmp_path_factory):
    """Download and extract rclone binary to a temporary directory."""
    # Create a temporary directory for the rclone binary
    temp_dir = tmp_path_factory.mktemp("rclone_bin")

    # Determine platform and architecture
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Map architecture names
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif machine in ("i386", "i686", "x86"):
        arch = "386"
    else:
        arch = "amd64"  # Default to amd64

    # Determine download URL and file extension
    if system == "windows":
        os_name = "windows"
        ext = "zip"
        exe_name = "rclone.exe"
    elif system == "darwin":
        os_name = "osx"
        ext = "zip"
        exe_name = "rclone"
    else:
        os_name = "linux"
        ext = "zip"
        exe_name = "rclone"

    # Download URL for latest stable version
    download_url = f"https://downloads.rclone.org/rclone-current-{os_name}-{arch}.{ext}"
    archive_path = temp_dir / f"rclone.{ext}"

    # Download the archive
    print(f"Downloading rclone from {download_url}...")
    urllib.request.urlretrieve(download_url, archive_path)

    # Extract the archive
    print(f"Extracting rclone to {temp_dir}...")
    if ext == "zip":
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
    else:
        with tarfile.open(archive_path, "r:gz") as tar_ref:
            tar_ref.extractall(temp_dir)

    # Find the extracted rclone binary
    # The archive extracts to a folder like "rclone-v1.xx.x-os-arch"
    for item in temp_dir.iterdir():
        if item.is_dir() and item.name.startswith("rclone"):
            binary_path = item / exe_name
            if binary_path.exists():
                # Make executable on Unix systems
                if system != "windows":
                    os.chmod(binary_path, 0o755)
                print(f"Rclone binary available at: {binary_path}")
                yield str(binary_path)
                return

    raise FileNotFoundError("Could not find rclone binary in extracted archive")


@pytest.fixture(autouse=True)
def reset_config(CUSTOM_PATH):
    """Ensure the singleton Config is reset to defaults before each test."""
    cfg = utils.Config()
    cfg.config_path = None
    cfg.executable_path = "rclone"
    yield
    # Reset again after test to avoid leak across files
    cfg.config_path = None
    cfg.executable_path = "rclone"


def test_set_executable_file(CUSTOM_PATH):
    """Test that set_executable_file correctly sets the executable path."""

    # Set custom executable
    rclone.set_executable_file(CUSTOM_PATH)

    # Get the config instance and verify the executable path was set
    config = utils.Config()
    assert config.executable_path == CUSTOM_PATH


def test_default_executable_path():
    """Test that the default executable path is 'rclone'."""
    config = utils.Config()
    # The default should be "rclone"
    assert config.executable_path == "rclone"


def test_set_executable_file_validation():
    """Test that set_executable_file validates the path when validate=True."""

    # Should raise FileNotFoundError for non-existent path
    with pytest.raises(FileNotFoundError):
        rclone.set_executable_file("/non/existent/path/rclone")

    # Should not raise when validate=False
    rclone.set_executable_file("/non/existent/path/rclone", validate=False)
    config = utils.Config()
    assert config.executable_path == "/non/existent/path/rclone"


def test_is_installed_with_custom_executable(tmp_path):
    """Test that is_installed() returns True when a valid custom executable is set."""

    # Create a fake executable file
    fake_rclone = tmp_path / "rclone.exe"
    fake_rclone.write_text("fake executable")

    # Mock which to return None (rclone not in PATH)
    with patch("rclone_python.rclone.which", return_value=None):
        # Without custom path, should return False
        assert rclone.is_installed() == False

        # Set custom executable path (skip validation since it's not a real executable)
        rclone.set_executable_file(str(fake_rclone), validate=False)

        # Now should return True
        assert rclone.is_installed() == True


def test_executable_used_in_command(CUSTOM_PATH):
    """Test that the custom executable is actually used when running rclone commands."""

    # Set custom executable (skip validation for mock path)
    rclone.set_executable_file(CUSTOM_PATH, validate=False)

    # Mock subprocess.run to capture the command being executed and bypass rclone presence check
    with patch("rclone_python.rclone.is_installed", return_value=True), patch(
        "rclone_python.utils.subprocess.run"
    ) as mock_run:
        # Setup mock to return successful result
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "[]"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        rclone.get_remotes()

        # Verify that subprocess.run was called
        assert mock_run.called

        # Get the command that was executed
        call_args = mock_run.call_args
        executed_command = call_args[0][0]

        # Verify the custom executable is in the command
        assert CUSTOM_PATH in executed_command

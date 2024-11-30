import hashlib
from pathlib import Path
import shutil

import pytest
from rclone_python import rclone
from rclone_python.hash_types import HashTypes


def _computeHash(file: str, hash_function=hashlib.sha1):
    with open(file, "rb") as file_to_check:
        # read contents of the file
        data = file_to_check.read()
        # pipe contents of the file through
        return hash_function(data).hexdigest()


hash_mapper = {
    HashTypes.sha1: hashlib.sha1,
    HashTypes.sha256: hashlib.sha256,
    HashTypes.md5: hashlib.md5,
}


def test_hash_single_file(default_test_setup):
    for hash_type, hash_function in hash_mapper.items():
        assert rclone.hash(
            hash=hash_type,
            path=default_test_setup.local_test_txt_file,
        ) == _computeHash(
            default_test_setup.local_test_txt_file, hash_function=hash_function
        )


def test_hash_multiple_files(default_test_setup, tmp_local_folder):
    shutil.copy(default_test_setup.local_test_txt_file, tmp_local_folder / "text_1.txt")
    shutil.copy(default_test_setup.local_test_txt_file, tmp_local_folder / "text 2.txt")
    shutil.copy(
        default_test_setup.local_test_txt_file, tmp_local_folder / "text  3.txt"
    )
    another = Path(tmp_local_folder / "another.txt")
    another.write_text(
        "Some other text that does not match that of the previous 3 files."
    )

    for hash_type, hash_function in hash_mapper.items():
        hash_text = _computeHash(
            default_test_setup.local_test_txt_file, hash_function=hash_function
        )
        hash_another = _computeHash(another, hash_function=hash_function)
        output = rclone.hash(
            hash=hash_type,
            path=tmp_local_folder,
        )
        # hash on multiple files returns a dict
        assert isinstance(output, dict)
        assert len(output) == 4

        # check that the hashes are correct
        assert output["text_1.txt"] == hash_text
        assert output["text 2.txt"] == hash_text
        assert output["text  3.txt"] == hash_text
        assert output["another.txt"] == hash_another


@pytest.mark.parametrize(
    "should_fail",
    [False, True],
)
def test_hash_with_checkfile_on_single_file(
    default_test_setup, tmp_local_folder, should_fail: bool
):
    checkfile = Path(tmp_local_folder / "checkfile")
    textfile = default_test_setup.local_test_txt_file

    for hash_type, hash_function in hash_mapper.items():
        hash = (
            _computeHash(textfile, hash_function=hash_function)
            if not should_fail
            else "random_hash_that_does_not_match"
        )
        checkfile.write_text(f"{hash}  {textfile.name}")

        output = rclone.hash(hash_type, textfile, checkfile=checkfile)
        assert isinstance(output, bool)
        assert output == (not should_fail)


def test_hash_with_checkfile_on_multiple_files(default_test_setup, tmp_local_folder):
    text_folder = tmp_local_folder / "text files"
    text_folder.mkdir(exist_ok=True)

    text_files = ["text_1.txt", "text_ 2.txt", "text_  3.txt"]
    faulty_files = ["faulty_1.txt", "faulty_ 2.txt", "faulty_  3.txt"]

    for f_name in text_files + faulty_files:
        shutil.copy(default_test_setup.local_test_txt_file, text_folder / f_name)

    checkfile = Path(tmp_local_folder / "checkfile")

    for hash_type, hash_function in hash_mapper.items():
        # manually write the hash file.
        # set a wrong hash for all faulty files.
        content = ""
        for i, file in enumerate(text_folder.iterdir()):
            hash = (
                _computeHash(file, hash_function=hash_function)
                if not file.name in faulty_files
                else f"faulty_hash_123456_{i}"
            )
            content += f"{hash}  {file.name}\n"
        checkfile.write_text(content)

        output = rclone.hash(hash_type, text_folder, checkfile=checkfile)
        assert isinstance(output, dict)

        for f_name in text_files:
            assert output[f_name] is True

        for f_name in faulty_files:
            assert output[f_name] is False


def test_hash_with_output_file(default_test_setup, tmp_local_folder):
    text_folder = tmp_local_folder / "text files"
    text_folder.mkdir(exist_ok=True)

    text_files = [
        Path(text_folder / "text_1.txt"),
        Path(text_folder / "text_ 2.txt"),
        Path(text_folder / "text_  3.txt"),
    ]
    output_file = Path(tmp_local_folder / "output-file")

    for file in text_files:
        shutil.copy(default_test_setup.local_test_txt_file, file)
    another = Path(text_folder / "another_file.txt")
    another.write_text("Something else....")
    text_files.append(another)

    for hash_type, hash_function in hash_mapper.items():
        rclone.hash(hash=hash_type, path=text_folder, output_file=output_file)

        assert output_file.is_file()
        assert len(output_file.read_text().splitlines()) == len(text_files)

        output = output_file.read_text()

        print(output)

        for file in text_files:
            assert (
                f"{_computeHash(file,hash_function=hash_function)}  {file.name}"
                in output
            )

from setuptools import setup

from rclone_python import VERSION

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="rclone-python",
    version=VERSION,
    description="A python wrapper for rclone.",
    author="Johannes Gundlach",
    url="https://github.com/Johannes11833/rclone_python",
    install_requires=["rich"],
    packages=["rclone_python"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["rclone", "wrapper", "cloud sync"],
    python_requires=">=3.6",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

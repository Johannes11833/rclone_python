from setuptools import setup

from py_rclone.rclone import get_version

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='py-rclone',
    version=get_version(),
    description='A python wrapper for rclone.',
    author='Johannes Gundlach',
    install_requires=['simple_term_menu', 'alive-progress', ],
    packages=['py_rclone'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=['rclone', 'wrapper', 'cloud sync'],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

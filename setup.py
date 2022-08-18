from setuptools import setup

from py_rclone import VERSION

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='rclone-python',
    version=VERSION,
    description='A python wrapper for rclone.',
    author='Johannes Gundlach',
    install_requires=['alive-progress'],
    packages=['py_rclone'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=['rclone', 'wrapper', 'cloud sync'],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)

from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='rclone_python',
    version='0.1',
    description='A python wrapper for rclone.',
    author='Johannes Gundlach',
    author_email='johannesgundlach97@gmail.com',
    install_requires=['simple_term_menu', 'alive-progress', ],
    packages=['rclone_python'],
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=['rclone', 'wrapper', 'cloud sync'],
)

from setuptools import setup

setup(
    name='rclone_python',
    version='0.1',
    description='A python wrapper for rclone.',
    author='Johannes Gundlach',
    author_email='johannesgundlach97@gmail.com',
    install_requires=['simple_term_menu', 'alive-progress', ],
    packages=['rclone_python'],
)

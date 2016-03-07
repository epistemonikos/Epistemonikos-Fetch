import os
from setuptools import setup, find_packages
import subprocess


git_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".git")
current_tag = subprocess.check_output(['git', '--git-dir', git_path, 'tag']).strip().split('\n')[-1]

setup(
    name='episte_fetch',
    version=current_tag,
    description="",
    long_description="""\
""",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Epistemonikos',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'lxml',
        'html_jumping',
        'selenium',
        'cssselect'
    ],
    entry_points="""
    # -*- Entry points: -*-
    """,
)

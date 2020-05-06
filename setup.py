from setuptools import find_packages, setup

from txt2hpo import __project__, __version__

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
name=__project__,
    packages=find_packages(),
    version=__version__,
    description='HPO concept recognition and phenotype extraction tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Vlad Gainullin <vgainullin@genedx.com>, Kevin Arvai <karvai@genedx.com>',
    author_email='<datascience@genedx.com>',
    license='',
    entry_points={
        'console_scripts': [
            f'{__project__} = {__project__}.__main__:main',
        ]
    },
    install_requires=[
        'phenopy',
        'pandas',
        'nltk',
        'spacy',
        'scispacy',
        'negspacy',
        'networkx',
        'gensim',
        'en_core_sci_sm'


    ],
    dependency_links=['https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.2.4/en_core_sci_sm-0.2.4.tar.gz#egg=en_core_sci_sm']
)

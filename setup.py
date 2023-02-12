import os
import subprocess
from setuptools import find_packages, setup


def get_version():
    path = os.path.abspath(os.path.join('inex', 'version.txt'))
    assert os.path.isfile(path), f'File {path} does not exist'
    with open(path) as stream:
        version = stream.read().strip()
    return version


def get_version_sha():
    try:
        sha = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()
        sha = sha[:5]
    except Exception:
        sha = 'failed-to-get-sha'
    return f'{get_version()}.{sha}'


path = os.path.join('inex', 'version.py')
with open(path, "wt") as stream:
    print(f"__version__ = '{get_version_sha()}'", file=stream)


with open('README.md', encoding='utf-8') as stream:
    long_description = stream.read()


setup(
    name='inex',
    version=get_version(),
    python_requires='>=3.6',
    author='Yuri Khokhlov',
    author_email='khokhlov@speechpro.com',
    description='inex: Microkernel',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache Software License',
    url="https://nid-gitlab.ad.speechpro.com/asr2/inex",
    project_urls={
        "Bug Tracker": "https://nid-gitlab.ad.speechpro.com/asr2/inex/issues",
    },
    install_requires=[
        'omegaconf>=2.2.3',
        'pytest>=7.2.0',
        'tox>=3.27.1',
        'numpy>=1.23.5',
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'inex = inex.inex:main',
        ]
    },
)

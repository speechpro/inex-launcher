import os
import subprocess
from setuptools import find_packages, setup


def get_version():
    path = os.path.abspath(os.path.join('mkernel', 'version.txt'))
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


path = os.path.join('mkernel', 'version.py')
with open(path, "wt") as stream:
    print(f"__version__ = '{get_version_sha()}'", file=stream)


with open('README.md', encoding='utf-8') as stream:
    long_description = stream.read()


setup(
    name='mkernel',
    version=get_version(),
    python_requires='>=3.6',
    author='Yuri Khokhlov',
    author_email='khokhlov@speechpro.com',
    description='mkernel: Microkernel',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache Software License',
    url="https://nid-gitlab.ad.speechpro.com/asr2/mkernel",
    project_urls={
        "Bug Tracker": "https://nid-gitlab.ad.speechpro.com/asr2/mkernel/issues",
    },
    install_requires=[
        'PyYAML>=6.0.0',
        'pytest>=7.1.2',
        'tox>=3.25.1',
        'numpy',
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'mkernel = mkernel.mkernel:main',
        ]
    },
)

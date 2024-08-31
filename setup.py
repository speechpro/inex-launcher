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
        sha = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
        sha = sha[:5]
    except Exception:
        sha = 'failed-to-get-sha'
    return f'{get_version()}.{sha}'


path = os.path.join('inex', 'version.py')
with open(path, 'wt') as stream:
    print(f"__version__ = '{get_version_sha()}'", file=stream)


with open('README.md', encoding='utf-8') as stream:
    long_description = stream.read()


setup(
    name='inex-launcher',
    version=get_version(),
    python_requires='>=3.6',
    author='Yuri Khokhlov',
    author_email='khokhlov@speechpro.com',
    description='InEx is a lightweight highly configurable Python launcher based on microkernel architecture',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url='https://github.com/speechpro/inex',
    project_urls={
        'Bug Tracker': 'https://github.com/speechpro/inex/issues',
    },
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
    ],
    install_requires=[
        'omegaconf',
        'networkx',
        'pytest',
        'tox',
    ],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    keywords='speechpro inex command-line configuration yaml',
    entry_points={
        'console_scripts': [
            'inex = inex.inex:main',
        ]
    },
)

from setuptools import setup, find_packages

setup(
    name='NADetector',
    version='0.1',
    packages=find_packages,
    author='Nick Anthony',
    author_email='nicholas.anthony@northwestern.edu',
    install_requires=[
        'PyQt5',
        'Instrumental-lib',
        'scikit-image',
        'pywin32',
        'nicelib'
    ],
    entry_points={'gui_scripts': [
        'NADetector = nadetector.__main__:main',
    ]},
    package_data={'NADetector': ['drivers/uc480_64.dll']},
)
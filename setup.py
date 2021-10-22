from setuptools import setup, find_packages

setup(
    name='nadetector',
    version='0.0.3',
    author='Nick Anthony',
    description='A GUI to assist in precisely setting the numerical aperture on a microscope.',
    author_email='nicholas.anthony@northwestern.edu',
    python_requires='>3.7',
    install_requires=[
        'PyQt5',
        'instrumental-lib',
        'scikit-image',
        'pywin32',
        'nicelib'
    ],
    package_dir={'': 'src'},
    package_data={'nadetector': ['_resources/*']},
    packages=find_packages('src'),
    entry_points={'gui_scripts': [
        'nadetector = nadetector.__main__:main',
    ]}
)
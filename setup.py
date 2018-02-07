from setuptools import setup

setup(
    name='airtablemock',
    version='0.0.3',
    packages=['airtablemock'],
    install_requires=['mock>=2.0.0'],
    tests_require=['airtable', 'pytest'],
    setup_requires=['pytest-runner'],
    description='Mock library for the airtable client',
    author='Pascal Corpet',
    url='https://github.com/bayesimpact/airtablemock',
    keywords=['airtable', 'api', 'mock'],
    license='The MIT License (MIT)',
)

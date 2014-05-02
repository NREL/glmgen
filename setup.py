from distutils.core import setup

setup(
    name='glm-utilities',
    version='0.1.0',
    author='TBD',
    author_email='TBD',
    packages=['glm-utilities', 'glm-utilities.test'],
    scripts=[],
    url='TBD',
    license='LICENSE.txt',
    description='Utilities for manipulating GridLAB-D model (glm) files in Python.',
    long_description=open('README.txt').read(),
    install_requires=open('requirements.txt').read(),
)
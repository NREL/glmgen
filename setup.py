from distutils.core import setup
import glmgen

setup(
    name='glmgen',
    version=glmgen.__version__,
    author='Elaine Hale, forked from https://github.com/elainethale/omf',
    author_email='elaine.hale@nrel.gov',
    packages=['glmgen', 'glmgen.test', 'glmgen.schedules'],
    package_data={'': ['*.glm', '*.player', '*.csv']},
    url='https://github.nrel.gov/ESI/omf-glm-generator',
    description='Utilities for manipulating GridLAB-D model (glm) files in Python.',
    install_requires=open('requirements.txt').read(),
)
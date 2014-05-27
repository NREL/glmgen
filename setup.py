from distutils.core import setup

setup(
    name='glmgen',
    version='0.1.0',
    author='TBD',
    author_email='TBD',
    packages=['glmgen', 'glmgen.test', 'glmgen.schedules'],
    package_data={'': ['*.glm', '*.player', '*.csv']},
    scripts=[],
    url='https://github.nrel.gov/ESI/omf-glm-generator',
    description='Utilities for manipulating GridLAB-D model (glm) files in Python.',
    install_requires=open('requirements.txt').read(),
)

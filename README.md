# omf-glm-generator

Private version of public fork https://github.com/elainethale/omf. Forking to use PNNL's latest taxonomy feeder generator code as a starting point for scripted generation of glm files. (The omf project is a web application to make it easier for MILSOFT users to evaluate grid technology changes.)

## Create and/or Install a Package

```bash
python setup.py sdist
```

This creates a .zip in `/dist`.

To install (change slash direction for Windows, use a different version as appropriate), 

```bash
pip install dist/glmgen-0.1.0.zip
```

## Running tests -- Peregrine

Basic setup:
```bash
module purge
# currently tested with python 2.7
module load epel python/2.7.6
cd /scratch/username/
git clone git@github.nrel.gov:ESI/omf-glm-generator.git
```

Make, activate, and populate a [virtual environment](http://hpc.nrel.gov/users/software/dev-tools/python):
```bash
cd ~
mkdir myvirtualenvs 
cd myvirtualenvs
virtualenv omf-glm-generator
. omf-glm-generator/bin/activate
pip install -r /scratch/username/omf-glm-generator/requirements.txt
pip install -I nose
```

Run the tests with this environment activated:
```bash
cd /scratch/username/omf-glm-generator/creators
export PYTHONPATH=${PYTHONPATH}:/scratch/username/omf-glm-generator/glm-utilities/
nosetests
```

Deactivate the virtual environment:
```bash
deactivate
```



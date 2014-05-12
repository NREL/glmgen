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

To uninstall before doing development or installing a new version,

```bash
pip uninstall glmgen
```


# omf-glm-generator

Private version of public fork https://github.com/elainethale/omf. Forking to use PNNL's latest taxonomy feeder generator code as a starting point for scripted generation of glm files. (The omf project is a web application to make it easier for MILSOFT users to evaluate grid technology changes.)

#### Install

`pip install git+ssh://git@github.nrel.gov/ESI/omf-glm-generator.git@master`

or 

`pip install git+ssh://git@github.nrel.gov/ESI/omf-glm-generator.git@v1.0.1`

Previous versions are listed at https://github.nrel.gov/ESI/omf-glm-generator/releases.

Unfortunately on Windows, while this command nominally works (after running it, `pip list` will show glmgen as installed), it [exits with errors](http://stackoverflow.com/q/23938896/1470262).

#### Uninstall

`pip uninstall glmgen`

#### Develop

1. Uninstall
2. [Set-up github.nrel.gov](https://github.nrel.gov/ehale/git-training#prerequisites-set-up-githubnrelgov)
3. Clone this repository
4. Add the top-level directory of the cloned repository to your PYTHONPATH
5. Follow a basic git workflow (branch on GitHub, checkout the branch locally, do your work, *commit, push, repeat from *, pull request)

#### Release

1. Make sure that all the changes to be put into the release have made their way into the develop branch.
2. Revisit the current version numbers in glmgen/__init__.py, on master and on develop. Update the version number on develop according to what changes were made during the last release cycle and the guidelines at [Semantic Versioning 2.0.0](http://semver.org/).
3. Update CHANGES.txt.
4. Optionally update setup.py and MANIFEST.in.
5. Update the install line in this file to point to the new (soon-to-be) version.
6. Merge develop into master. 
7. Create a tag on master following the format 'v{}.{}.{}'.format(major,minor,patch).


# glmgen

Fork of the [Open Modeling Framework (OMF)](https://github.com/dpinney/omf) that has been pruned down to just its functionality for editing glm files, and then further developed in that direction.

#### Install

`pip install git+https://github.com/NREL/glmgen.git@master`

or 

`pip install git+https://github.com/NREL/glmgen.git@v4.1.0`

Previous versions are listed at https://github.com/NREL/glmgen/releases.

Unfortunately on Windows, while this command nominally works (after running it, `pip list` will show glmgen as installed), it [exits with errors](http://stackoverflow.com/q/23938896/1470262).

#### Starting points

- glmgen.feeder.GlmFile
- glmgen.makeGLM.makeGLM

This code is used in a research project that primarily uses the [PNNL Taxonomy Feeders](http://sourceforge.net/p/gridlab-d/code/HEAD/tree/Taxonomy_Feeders/) ([doc](http://www.gridlabd.org/models/feeders/taxonomy_of_prototypical_feeders.pdf)) as a starting point to develop feeder models populated with houses and solar.

#### Uninstall

`pip uninstall glmgen`


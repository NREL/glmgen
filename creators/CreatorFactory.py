
import json
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator
from ComputationalStudyCreator import ComputationalStudyParams

def load(path_or_dict):
    if isinstance(path_or_dict,dict):
        d = path_or_dict
        # dispatch to concrete classes by d["class_name"]
        if d["class_name"] == ComputationalCaseParams.class_name:
            return ComputationalCaseParams.load(d)
        elif d["class_name"] == ComputationalStudyParams.class_name:
            creator = load(d["sub_creator"])
            return ComputationalStudyParams.load(d,creator)
        elif d["class_name"] == ComputationalCaseCreator.class_name:
            return ComputationalCaseCreator.load(d)
        else:
            raise RuntimeError("{:s} cannot yet be deserialized.".format(d["class_name"]))    
    else:
        # load json from path
        f = open(path_or_dict,'r')
        obj = json.load(f)
        f.close()
        assert(isinstance(obj,dict))
        # forward request to dict loader
        return load(obj)

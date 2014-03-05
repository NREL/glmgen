
from CreatorBase import Params, ParamDescriptor, Creator, base_path

import datetime
import numpy
import os
import pandas

def find_feeder(feeder):
    """
    Tries to finds a feeder glm file from feeder. Raises a RuntimeError if it cannot be located.
    
    @type feeder: string
    @param feeder: Glm file name or full path. If just a file name, looks in data/Feeder
    """
    result = os.path.realpath(feeder)
    if not os.path.exists(result):
        result = os.path.realpath(base_path() + "/data/Feeder/" + feeder)
    if not os.path.exists(result):
        raise RuntimeError("Cannot locate feeder '{:s}'.".format(feeder))   
    return result
    
def installed_feeders():
    result = []
    feeder_path = os.path.realpath(base_path() + "/data/Feeder/")
    for subdir, dirs, files in os.walk(feeder_path):
        for file in files:
            result.append(file)

def find_sub_template():
    result = os.path.realpath(feeder)
    if not os.path.exists(result):
        result = os.path.realpath(base_path() + "/data/Templates/" + feeder)
    if not os.path.exists(result):
        raise RuntimeError("Cannot locate template batch file '{:s}'.".format(feeder))   
    return result

def installed_sub_templates():
    result = []
    feeder_path = os.path.realpath(base_path() + "/data/Templates/")
    for subdir, dirs, files in os.walk(feeder_path):
        for file in files:
            result.append(file)
    
def to_timedelta(timedelta): 
    """
    Tries to convert timedelta to a real datetime.timedelta. Raises a RuntimeError if not successful.
    """
    try:
        if type(timedelta) in [type(datetime.timedelta()), type(numpy.timedelta64())]:
            return timedelta
        else:
            return pandas.to_timedelta(timedelta)
    except:
        raise RuntimeError("Could not convert {:s} to datetime.timedelta.".format(timedelta))

class ComputationalCaseParams(Params):         

    def __init__(self, values = {}):
        schema = {}
        schema["base_feeder"] = ParamDescriptor(
            "base_feeder",
            "Name of glm file in data/Feeder, or full path to glm file.",
            0,
            True,
            None,
            find_feeder,
            installed_feeders)
        schema["sim_duration"] = ParamDescriptor(
            "sim_duration",
            "How long the gridlabd simulation should run.",
            1,
            False,
            datetime.timedelta(hours=1),
            to_timedelta)
    #     schema["sim_timestep"] = ParamDescriptor(
    #         "sim_timestep",
    #         "Minimum gridlabd timestep.",
    #         2,
    #         False,
    #         datetime.timedelta(minutes=1),
    #         to_timedelta)
    #     schema["technolgies"] = ParamDescriptor(
    #         "technologies",
    #         "Technologies to apply to the feeder.",
    #         3,
    #         False,
    #         [0])
        schema["case_name"] = ParamDescriptor(
            "case_name",
            "User defined case name. Will compose one from other parameters if not provided.",
            2,
            False)
        schema["sub_template"] = ParamDescriptor(
            "sub_template",
            "Batch submission script template.",
            3,
            False,
            None,
            find_sub_template,
            installed_sub_templates)
        Params.__init__(self, schema, values)

    def load(path): pass        

class ComputationalCaseCreator(Creator): pass

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
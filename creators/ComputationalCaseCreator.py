
from CreatorBase import Params, ParamDescriptor, Creator

import datetime

def find_feeder(feeder): pass
    """
    Tries to finds a feeder glm file from feeder. Raises a RuntimeError if it cannot be located.
    
    @type feeder: string
    @param feeder: Glm file name or full path. If just a file name, looks in data/Feeder
    """
    
def to_timedelta(timedelta): 
    """
    Tries to convert timedelta to a real datetime.timedelta. Raises a RuntimeError if not successful.
    """
    try:
        return datetime.timedelta(timedelta)
    except:
        raise RuntimeError(print("Could not convert ",timedelta," to datetime.timedelta."))

class ComputationalCaseParams(Params): 
    __schema = {}
    __schema["base_feeder"] = ParamDescriptor(
        "base_feeder",
        "Name of glm file in data/Feeder, or full path to glm file.",
        0,
        True,
        None,
        find_feeder)
    __schema["sim_duration"] = ParamDescriptor(
        "sim_duration",
        "How long the gridlabd simulation should run.",
        1,
        False,
        datetime.timedelta(hours=1),
        to_timedelta)
    # __schema["sim_timestep"] = ParamDescriptor(
    #     "sim_timestep",
    #     "Minimum gridlabd timestep.",
    #     2,
    #     False,
    #     datetime.timedelta(minutes=1),
    #     to_timedelta)
    # __schema["technolgies"] = ParamDescriptor(
    #     "technologies",
    #     "Technologies to apply to the feeder.",
    #     3,
    #     False,
    #     [0])

    def __init__(self, values = {}):
        Params.__init__(values)

    def load(path): pass        

class ComputationalCaseCreator(Creator): pass

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
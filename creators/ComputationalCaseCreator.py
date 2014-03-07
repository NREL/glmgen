
from CreatorBase import Params, ParamDescriptor, Creator, base_path

import feeder
from makeGLM import makeGLM

import datetime
import numpy
import os
import pandas
import shutil

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

class ComputationalCaseCreator(Creator): 
    """
    Class for creating a glm file, in its own run directory, along with needed resources and (optionally), a 
    batch submission script.
    """
    def __init__(self, out_dir, params, resources_dir = None):
        """
        Get ready to make a new glm file in its own run directory.
        
        @type out_dir: path 
        @param out_dir: Parent directory of the case directory to be created.
        @type params: ComputationalCaseParams
        @param params: Object containing the parameters to use in making this case.
        @type resources_dir: path
        @param resources_dir: Optional (shared) directory where resources are to be stored.
        """
        if not isinstance(params, ComputationalCaseParams):
            raise RuntimeError("ComputationalCaseCreator must be instantiated with a valid instance of ComputationalCaseParams.")
        Creator.__init__(self,out_dir, params, resources_dir)
        
    def create(self):    
        # switch to out_dir or parent of out_dir; make out_dir if needed
        if not os.path.exists(self.out_dir):
            if os.path.exists(os.path.dirname(self.out_dir)):
                os.mkdir(self.out_dir)
            else:
                raise RuntimeError("Parent directory of '{:s}' does not exist. Cannot make out_dir.".format(self.out_dir))
        original_dir = os.getcwd()
        os.chdir(self.out_dir)
        
        # get or make case_name
        case_name = self.params.get("case_name")
        if case_name is None:
            case_name = "{:s}_{:s}".format(self.__base_feeder_name(),self.__sim_duration_dhm())
        
        # make case folder
        if os.path.exists(case_name):
            shutil.rmtree(case_name)
        os.mkdir(case_name)
        
        # make glm file and save to case folder
        glm_dict = feeder.parse(self.params.get("base_feeder"))
        generated_taxonomy_feeder_paths = makeGLM(self.__get_clock(),None,glm_dict,0,None,case_name)
                
        # get and save or verify resources
        schedules_dir = os.path.realpath(case_name + "/schedules")
        schedules_source_dir = os.path.realpath(base_path() + "/glm-utilities/schedules")
        shutil.copytree(schedules_source_dir,schedules_dir)
        
        # populate sub template and save to case folder
        
        os.chdir(original_dir)
        
        
    def __base_feeder_name(self):
        """
        The "base_feeder" parameter is guaranteed by CreatorBase.__init__ insisting that params be
        valid. Then we split any directories, and then the extension, off of the base_feeder glm path.
        
        @rtype: string
        @return: The base feeder glm file's name, divorced from parent directories and file extension.
        """
        return os.path.splitext(os.path.split(self.params.get("base_feeder"))[1])[0]
        
    def __sim_duration_dhm(self):
        dt = self.params.get("sim_duration")
        n_days = dt.days
        n_hours = dt.seconds // 3600
        n_mins = (dt.seconds // 60 ) % 60
        result = ""
        if n_days > 0: result += "{:s}d".format(n_days) 
        if n_hours > 0: result += "{:d}h".format(n_hours)
        if n_mins > 0: result += "{:d}m".format(n_mins)
        return result
        
    def __get_clock(self):
        sim_start = datetime.datetime(2020,6,1,0)
        sim_duration = self.params.get("sim_duration")
        warmup_duration = datetime.timedelta(0)
        clock = {}
        clock[str(sim_start)] = [str(sim_start - warmup_duration),
                                 str(sim_start + sim_duration)]
        return clock


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

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
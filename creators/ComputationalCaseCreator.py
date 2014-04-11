
from CreatorBase import Params, ParamDescriptor, Creator
from CreatorBase import base_path, to_timedelta, installed_sub_templates, to_walltime

import feeder
from makeGLM import makeGLM

import jinja2

import datetime as dt
import os
import pandas
import shutil

class ComputationalCaseParams(Params):         

    class_name = "ComputationalCaseParams"
        
    def get_class_name(self):
        return ComputationalCaseParams.class_name

    def __init__(self, *arg, **kw):
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
            dt.timedelta(hours=1),
            to_timedelta)
    #     schema["sim_timestep"] = ParamDescriptor(
    #         "sim_timestep",
    #         "Minimum gridlabd timestep.",
    #         2,
    #         False,
    #         dt.timedelta(minutes=1),
    #         to_timedelta)
        schema["technology"] = ParamDescriptor(
            "technology",
            "Technology case to apply to the feeder.",
            2,
            False,
            0,
            None,
            [-1,0,1,2,3,4,5,6,7,8,9,10,11,12,13])
        schema["case_name"] = ParamDescriptor(
            "case_name",
            "User defined case name. Will compose one from other parameters if not provided.",
            3,
            False)
        schema["sub_template"] = ParamDescriptor(
            "sub_template",
            "Batch submission script template.",
            4,
            False,
            None,
            None, # jinja2 FileSystemLoader handles the default location
            installed_sub_templates)
        schema["compute_efficiency"] = ParamDescriptor(
            "compute_efficiency",
            "Ratio of simulated time to computation time (e.g. 100 for '100 times faster than real time'). Used to set walltime in the batch submission script.",
            5,
            False,
            100.0)            
            
        Params.__init__(self, schema, *arg, **kw)
        
    @staticmethod
    def load(json_dict): 
        result = ComputationalCaseParams()
        for key, item in json_dict.items():
            if not (key == "class_name"):
                result[key] = item
        return result

class ComputationalCaseCreator(Creator): 
    """
    Class for creating a glm file, in its own run directory, along with needed resources and (optionally), a 
    batch submission script.
    """
    
    class_name = "ComputationalCaseCreator"
        
    def get_class_name(self):
        return ComputationalCaseCreator.class_name
    
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
        case_name = self.params["case_name"]
        if case_name is None:
            case_name = "{:s}_{:s}_t{:d}".format(self.__base_feeder_name(),
                                                 self.__sim_duration_dhm(),
                                                 self.params["technology"])
        
        # make case folder
        if os.path.exists(case_name):
            shutil.rmtree(case_name)
        os.mkdir(case_name)
        
        # make glm file and save to case folder
        glm_dict = feeder.parse(self.params["base_feeder"])
        generated_taxonomy_feeder_paths = makeGLM(self.__get_clock(),
                                                  None,
                                                  glm_dict,
                                                  self.params["technology"],
                                                  None,
                                                  case_name)
        glm_file_name = "model.glm"
        for subdir, dirs, files in os.walk(case_name):
            for file in files:
               if os.path.splitext(file)[1] == ".glm":
                   print("Renaming {:s}/{:s} to {:s}/{:s}.".format(case_name,file,case_name,glm_file_name))
                   shutil.move(os.path.realpath(case_name + "/" + file),
                               os.path.realpath(case_name + "/" + glm_file_name))
                
        # get and save or verify resources
        schedules_dir = os.path.realpath(case_name + "/schedules")
        schedules_source_dir = os.path.realpath(base_path() + "/glm-utilities/schedules")
        shutil.copytree(schedules_source_dir,schedules_dir)
        
        # populate sub template and save to case folder
        template_path = self.params["sub_template"]
        if template_path is not None:        
            batch_job_walltime = dt.timedelta(seconds=(1.0/self.params["compute_efficiency"]) * 
                                              self.params["sim_duration"].total_seconds())
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath(base_path() + "/data/Templates")),
                                     trim_blocks=True,
                                     lstrip_blocks=True)
            template = env.get_template(template_path)
            things = {}
            things["to_walltime"] = to_walltime
            things["batch_job_walltime"] = batch_job_walltime
            things["case_name"] = case_name
            things["datetime"] = dt
            things["datetime.timedelta"] = dt.timedelta
            f = open(os.path.realpath(case_name + "/run_script.sub"),'w')
            f.write(template.render(things))
        
        os.chdir(original_dir)
        return case_name
        
    @staticmethod
    def load(json_dict): 
        return ComputationalCaseCreator(json_dict["out_dir"],
                                        ComputationalCaseParams.load(json_dict["params"]),
                                        json_dict["resources_dir"])        
        
    def __base_feeder_name(self):
        """
        The "base_feeder" parameter is guaranteed by CreatorBase.__init__ insisting that params be
        valid. Then we split any directories, and then the extension, off of the base_feeder glm path.
        
        @rtype: string
        @return: The base feeder glm file's name, divorced from parent directories and file extension.
        """
        return os.path.splitext(os.path.split(self.params["base_feeder"])[1])[0]
        
    def __sim_duration_dhm(self):
        sim_duration = self.params["sim_duration"]
        n_days = sim_duration.days
        n_hours = sim_duration.seconds // 3600
        n_mins = (sim_duration.seconds // 60 ) % 60
        result = ""
        if n_days > 0: result += "{:d}d".format(n_days) 
        if n_hours > 0: result += "{:d}h".format(n_hours)
        if n_mins > 0: result += "{:d}m".format(n_mins)
        return result
        
    def __get_clock(self):
        sim_start = dt.datetime(2020,6,1,0)
        sim_duration = self.params["sim_duration"]
        warmup_duration = dt.timedelta(0)
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
    return result        

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
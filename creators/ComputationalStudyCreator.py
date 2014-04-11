
from CreatorBase import Params, ParamDescriptor, Creator, create_choice_descriptor
from CreatorBase import base_path, to_timedelta, installed_sub_templates, to_walltime

import numpy
from pyDOE import lhs
from scipy.stats.distributions import uniform, randint

import jinja2

import copy
import datetime as dt
import math
import os
import re
import shutil

class ComputationalStudyParams(Params):
    """
    Parameters for specifying a computational study based on a Creator object. A few 
    parameters define the study type; most parameters are derived from 
    creator.params.schema(). In general, this class defines its schema iteratively, 
    that is, as parameter values are set, the schema may be modified.
    """
    class_name = "ComputationalStudyParams"    
        
    def get_class_name(self):
        return ComputationalStudyParams.class_name
    
    def __init__(self, creator, *arg, **kw): 
        schema = {}
        schema["study_type"] = create_choice_descriptor("study_type",
                                                        ["full_factorial","lhs"],
                                                        "Type of study to construct",
                                                        0)
        Params.__init__(self, schema, *arg, **kw)
        
        # now each param (argument) in creator can be fixed, list, or range
        choices = ["fixed","list","range"] # default is fixed
        index = 10
        self.__param_types = { "fixed": [], "list": [], "range": [] }
        for arg_name, arg_descriptor in sorted(creator.params.schema().items(), key=lambda pair: pair[1].index) :
            schema[self.param_name(arg_name)] = ParamDescriptor(
                self.param_name(arg_name),
                "Parameter to set to change how the Computational Study will treat {:s}. Pass in a fixed value, list, or tuple of length 2 (range).".format(arg_name),
                index,
                True,
                "processed")                
            schema[self.__param_type_param_name(arg_name)] = create_choice_descriptor(
                self.__param_type_param_name(arg_name),
                choices,
                "How {:s} values are to be sampled".format(arg_name),
                index+1,
                True,
                "fixed")
            self.__param_types["fixed"].append(arg_name)
            index += 10
            
        self.creator = creator
        
        schema["sub_template"] = ParamDescriptor(
            "sub_template",
            "Batch submission script template.",
            index,
            False,
            None,
            None, # jinja2 FileSystemLoader handles the default location
            installed_sub_templates)
        schema["time_per_job"] = ParamDescriptor(
            "time_per_job",
            "Approximate length of time per job (datetime.timedelta object).",
            index + 1,
            False,
            dt.timedelta(minutes=30),
            to_timedelta)
    
    def valid(self):
        result = Params.valid(self)
        if result:
            study_type = self.get("study_type")
            if (study_type == "full_factorial") and len(self.__param_types["range"]) > 0:
                result = False
                print("Full factorial studies require all param_types to be 'fixed' or 'list'.")
        return result
    
    def arg_names(self): 
        result = copy.deepcopy(self.__param_types["fixed"])
        result.extend(copy.deepcopy(self.__param_types["list"]))
        result.extend(copy.deepcopy(self.__param_types["range"]))
        return result
        
    def param_name(self,arg_name):
        return "{:s}_param".format(arg_name)
    
    def get_param_type(self, arg_name): 
        if arg_name in self.__param_types["fixed"]:
            return "fixed"
        if arg_name in self.__param_types["list"]:
            return "list"
        if arg_name in self.__param_types["range"]:
            return "range"
        raise RuntimeError("{:s} is not a known arg_name.".format(arg_name))
    
    def get_values_list(self, arg_name): 
        assert self.get_param_type(arg_name) == "list"
        return self[self.__values_list_param_name(arg_name)]
    
    def get_values_range(self, arg_name): 
        assert self.get_param_type(arg_name) == "range"
        return (self[self.__range_min_param_name(arg_name)],self[self.__range_max_param_name(arg_name)])
        
    def get_arg_values(self,include_fixed=False):
        """
        @rtype: List of tuples (arg_name, param_type, value(s)/range)
        """
        result = []
        for arg_name in self.arg_names():
            param_type = self.get_param_type(arg_name)
            if param_type == "fixed":
                if include_fixed:
                    result.append( (arg_name, param_type, self.creator.params[arg_name]) )
            elif param_type == "list":
                result.append( (arg_name, param_type, self.get_values_list(arg_name)) )
            else:
                assert (param_type == "range")
                result.append( (arg_name, param_type, self.get_values_range(arg_name)) )
        return result
        
    def to_json_dict(self):
        d = Params.to_json_dict(self)
        d["sub_creator"] = self.creator.to_json_dict()
        return d        
        
    @staticmethod
    def load(json_dict, creator): 
        result = ComputationalStudyParams(creator)
        
        # if possible, set the study type, and delete items already used
        if "study_type" in json_dict:
            result["study_type"] = json_dict["study_type"]
            del json_dict["study_type"]
        del json_dict["class_name"]
        del json_dict["sub_creator"]
        
        arg_name = None
        for key, item in sorted(json_dict.items()):
            if result.__is_arg_param(key):
                # process meta-parameters on arg_name
                arg_name = result.__get_arg_name(key)
                value = None
                param_type = json_dict[result.__param_type_param_name(arg_name)]
                if param_type == "fixed":
                    continue
                elif param_type == "list":
                    value = json_dict[result.__values_list_param_name(arg_name)]
                elif param_type == "range":
                    value = (json_dict[result.__range_min_param_name(arg_name)],
                             json_dict[result.__range_max_param_name(arg_name)])
                result[key] = value
            elif (arg_name is None) or (not re.match("{:s}_.*".format(arg_name),key)):
                # study parameter
                result[key] = item
        return result        
                
    def __param_type_param_name(self,arg_name):
        return "{:s}_param_type".format(arg_name)
    
    def __values_list_param_name(self,arg_name):
        return "{:s}_values_list".format(arg_name)
        
    def __range_min_param_name(self,arg_name):
        return "{:s}_range_min".format(arg_name)
                
    def __range_max_param_name(self,arg_name):
        return "{:s}_range_max".format(arg_name)
        
    def _Params__refresh_schema(self,param_name): 
        # the study_type was set
        if param_name == "study_type":
            study_type = self.get("study_type")
            if study_type == "lhs":
                if "num_samples" not in self._Params__schema:
                    self._Params__schema["num_samples"] = ParamDescriptor(
                        "num_samples",
                        "Number of samples to create for the study.",
                        1,
                        True,
                        None,
                        lambda x: int(x) if int(x) > 0 else None)
            elif "num_samples" in self._Params__schema:
                del self["num_samples"]
                del self._Params__schema["num_samples"]
                
        # a creator parameter type was set (to fixed, list, or range)
        if self.__is_arg_param(param_name):
            arg_name = self.__get_arg_name(param_name)
            
            # get value and determine param_type. nothing to do if value = "processed"
            param_value = self[param_name]
            if param_value == "processed":
                return
            param_type = "fixed"
            if isinstance(param_value,list):
                param_type = "list"
            elif isinstance(param_value,tuple):
                # we only recognize tuples of length 2
                if len(param_value) != 2:
                    raise RuntimeError("{:s} only accepts fixed values, lists, and tuples of length 2.".format(param_name))
                # is it a tuple that explicitly states param_type?
                if param_value[0] in self._Params__schema[self.__param_type_param_name(arg_name)].suggested_values:
                    param_type = param_value[0]
                    param_value = param_value[1]
                else:
                    param_type = "range"
            
            old_param_type = self.get_param_type(arg_name)
            if param_type != old_param_type:
                # set type
                self[self.__param_type_param_name(arg_name)] = param_type
            
                # adjust map
                self.__param_types[old_param_type] = \
                    [x for x in self.__param_types[old_param_type] if not (x == arg_name)]
                self.__param_types[param_type].append(arg_name)
                
                # adjust schema
                index = self._Params__schema[param_name].index
                values_list_param_name = self.__values_list_param_name(arg_name)
                range_min_param_name = self.__range_min_param_name(arg_name)
                range_max_param_name = self.__range_max_param_name(arg_name)
                value_parser = self.creator.params.schema()[arg_name].parser
                parser = value_parser
                if param_type == "fixed":
                    # delete any list parameters
                    if values_list_param_name in self._Params__schema:
                        del self[values_list_param_name]
                        del self._Params__schema[values_list_param_name]
                    # delete any range parameters
                    if range_min_param_name in self._Params__schema:
                        del self[range_min_param_name]
                        del self._Params__schema[range_min_param_name]
                    if range_max_param_name in self._Params__schema:
                        del self[range_max_param_name]
                        del self._Params__schema[range_max_param_name]
                    
                elif param_type == "list":
                    # ensure list parameters
                    if value_parser is not None:
                        parser = lambda lst: [value_parser(x) for x in lst]
                    self._Params__schema[values_list_param_name] = ParamDescriptor(
                        values_list_param_name,
                        "Enumerated list of values for {:s}.".format(arg_name),
                        index + 2,
                        True,
                        None,
                        parser)
                    # delete any range parameters
                    if range_min_param_name in self._Params__schema:
                        del self[range_min_param_name]
                        del self._Params__schema[range_min_param_name]
                    if range_max_param_name in self._Params__schema:
                        del self[range_max_param_name]
                        del self._Params__schema[range_max_param_name]                     
                        
                else:
                    assert (param_type == "range")
                    # ensure range paramters                  
                    self._Params__schema[range_min_param_name] = ParamDescriptor(
                        range_min_param_name,
                        "Minimum value in range for {:s}.".format(arg_name),
                        index + 2,
                        True,
                        None,
                        parser)                    
                    self._Params__schema[range_max_param_name] = ParamDescriptor(
                        range_max_param_name,
                        "Maximum value in range for {:s}.".format(arg_name),
                        index + 3,
                        True,
                        None,
                        parser)
                    # delete any list parameters
                    if values_list_param_name in self._Params__schema:
                        del self[values_list_param_name]
                        del self._Params__schema[values_list_param_name]  

            # set value
            if param_type == "fixed":
                self.creator.params[arg_name] = param_value
            elif param_type == "list":
                self[self.__values_list_param_name(arg_name)] = param_value
            else:
                assert (param_type == "range")
                self[self.__range_min_param_name(arg_name)] = param_value[0]
                self[self.__range_max_param_name(arg_name)] = param_value[1]
                
            # set param_name to "processed"
            self[param_name] = "processed"
                    
    def __is_arg_param(self,param_name): 
        """
        Returns true if param_name is of the form of "{:s}_param".format(arg_name).
        """
        return re.match('.+_param',param_name) and (not re.match('.+_param_type',param_name))
        
    def __get_arg_name(self,param_name): 
        """
        If self.__is_arg_param(param_name), returns the arg_name.
        """
        assert self.__is_arg_param(param_name)
        return re.match('(.+)_param',param_name).group(1)
        
    
class ComputationalStudyCreator(Creator):
    class_name = "ComputationalStudyCreator"
        
    def get_class_name(self):
        return ComputationalStudyCreator.class_name

    def __init__(self, out_dir, params, resources_dir = None): 
        """
        Get ready to create a computational study. 
        
        @type out_dir: path 
        @param out_dir: The output directory of the computational study. If it exists, its contents will be deleted first.
        @type params: ComputationalStudyParams
        @param params: Object containing the sub-creator and study parameters.
        @type resources_dir: path
        @param resources_dir: Optional (shared) directory where resources are to be stored.
        """
        if not isinstance(params, ComputationalStudyParams):
            raise RuntimeError("ComputationalStudyCreator must be instantiated with a valid instance of ComputationalStudyParams.")
        Creator.__init__(self,out_dir,params,resources_dir)
        
        # make sure sub-creator shares out_dir, resources_dir
        self.params.creator.out_dir = out_dir
        self.params.creator.resources_dir = resources_dir
                        
    def create(self): 
        # remove if necessary, and then make, out_dir
        if os.path.exists(self.out_dir):
            shutil.rmtree(self.out_dir)
        if os.path.exists(os.path.dirname(self.out_dir)):
            os.mkdir(self.out_dir)
        else:
            raise RuntimeError("Parent directory of '{:s}' does not exist. Cannot make out_dir.".format(self.out_dir))
            
        # get the study_type and related parameters
        # delegate work to the study_type-specific create method
        study_type = self.params["study_type"]
        if study_type == "lhs":
            num_samples = self.params["num_samples"]
            assert (num_samples is not None)
            self.__lhs(num_samples)
        else :
            assert study_type == "full_factorial"
            self.__full_factorial()
            
        return self.out_dir
                
    def __full_factorial(self): 
        # should only contain "list" arguments
        arg_values = self.params.get_arg_values()
        prev_points = [[]]
        current_points = [[]]
        arg_names = []
        for arg in arg_values: 
            arg_names.append(arg[0])
            assert (arg[1] == "list")
            first = True
            for value in arg[2]:
                if first:
                    for point in current_points:
                        point.append(value)
                else:
                    prev_points_copy = copy.deepcopy(prev_points)
                    for point in prev_points_copy:
                        point.append(value)
                    current_points.extend(prev_points_copy)
                first = False
            prev_points = copy.deepcopy(current_points)

        self.__run_sub_creator(arg_names,current_points)
    
    def __lhs(self,num_samples): 
        # can contain "list" and "range" arguments          
        arg_values = self.params.get_arg_values() # [(arg_name, param_type, value(s)/range)]
        lhs_design = lhs(len(arg_values), samples=num_samples)
        assert (len(lhs_design) == num_samples)        # list of samples
        assert (len(lhs_design[0]) == len(arg_values)) # each sample has value for each arg
        # convert lhs_design[i][j] values by mapping 0-1 to arg_values[j] with uniform distribution
        points = [] # same dimensions as lhs_design, to contain converted values
        for i in range(num_samples): points.append([])
        arg_index = 0
        arg_names = []
        for arg in arg_values:
            arg_names.append(arg[0])
        
            convert_function = None
            if arg[1] == "list":
                convert_function = lambda x: arg[2][(randint(0,len(arg[2])-1).ppf(x)).astype(numpy.int16)]
            else:
                assert (arg[1] == "range")
                transforms = to_from_number_transforms(arg[2][0])
                to_number = transforms[0]
                from_number = transforms[1]
                convert_function = lambda x: from_number(uniform(to_number(arg[2][0]),to_number(arg[2][1])).ppf(x))
                
            point_index = 0
            for lhs_point in lhs_design:
                points[point_index].append(convert_function(lhs_point[arg_index]))
                point_index += 1
            arg_index += 1
            
        assert (len(points) == num_samples)
        self.__run_sub_creator(arg_names,points)        
    
    def __run_sub_creator(self,arg_names,arg_values): 
        samples = []
        for point in arg_values:
            assert(len(arg_names) == len(point))
            index = 0
            for value in point:
                self.params.creator.params[arg_names[index]] = value
                index += 1
            case_name = self.params.creator.create()
            samples.append(case_name)
            
        # populate sub template and save to case folder
        template_path = self.params["sub_template"]
        if template_path is not None:        
            time_per_job = self.__round_time_per_job(self.params["time_per_job"])
            batch_job_walltime = dt.timedelta(seconds=((math.ceil(len(samples) / 24) + 1) * 
                                                      time_per_job.total_seconds()))
            if batch_job_walltime < dt.timedelta(minutes=15):
                batch_job_walltime = dt.timedelta(minutes=15)
            env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.realpath(base_path() + "/data/Templates")),
                                     trim_blocks=True,
                                     lstrip_blocks=True)
            template = env.get_template(template_path)
            things = {}
            things["to_walltime"] = to_walltime
            things["batch_job_walltime"] = batch_job_walltime
            things["study_name"] = os.path.basename(os.path.normpath(self.out_dir))
            things["datetime"] = dt
            things["datetime.timedelta"] = dt.timedelta
            things["range"] = range
            things["len"] = len
            things["samples"] = samples
            things["sleep_str"] = self.__to_sleep_str(time_per_job)
            f = open(os.path.realpath(self.out_dir + "/run_script.sub"),'w')
            f.write(template.render(things))     

    def __round_time_per_job(self,time_per_job):
        n_days = time_per_job.days
        n_hours = time_per_job.seconds // 3600
        n_mins = (time_per_job.seconds // 60 ) % 60
        n_secs = time_per_job.seconds % 60
        if n_days > 0:
            if n_hours > 0:
                n_days += 1
            return dt.timedelta(days=n_days)
        if n_hours > 0:
            if n_mins > 0:
                n_hours += 1
            return dt.timedelta(hours=n_hours)
        if n_mins > 0:
            if n_secs > 0:
                n_mins += 1
            return dt.timedelta(minutes=n_mins)
        if n_secs == 0:
            n_secs = 1
        return dt.timedelta(seconds=n_secs)
        
    def __to_sleep_str(self,time_per_job):
        n_days = time_per_job.days
        n_hours = time_per_job.seconds // 3600
        n_mins = (time_per_job.seconds // 60 ) % 60
        n_secs = time_per_job.seconds % 60
        if n_days > 0:
            return "{:d}d".format(n_days)
        if n_hours > 0:
            return "{:d}h".format(n_hours)
        if n_mins > 0:
            return "{:d}m".format(n_mins)
        return "{:d}s".format(n_secs)
            
def to_from_number_transforms(obj):
    """
    Returns a pair of functions for converting obj to a number, and converting a 
    number back into an obj. Default implementation is a pair of identity functions.
    
    Non-default implementations:
        - datetime.timedelta
    
    @rtype: (function, function)
    @return: First function in tuple is to_number(obj) function. Second is from_number(num).
    """
    if isinstance(obj, dt.timedelta):
        return (lambda x: x.total_seconds(), lambda x: dt.timedelta(seconds=x))
    return (lambda x: x, lambda x: x)

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
    
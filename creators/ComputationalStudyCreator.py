
from CreatorBase import Params, ParamDescriptor, Creator, create_choice_descriptor

import numpy
from pyDOE import lhs
from scipy.stats.distributions import uniform, randint

import copy
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
    def __init__(self, creator, values = {}): 
        schema = {}
        schema["study_type"] = create_choice_descriptor("study_type",
                                                        ["full_factorial","lhs"],
                                                        "Type of study to construct",
                                                        0)
        Params.__init__(self, schema, values)
        
        # now each param (argument) in creator can be fixed, list, or range
        choices = ["fixed","list","range"] # default is fixed
        index = 10
        self.__param_types = { "fixed": [], "list": [], "range": [] }
        for arg_name, arg_descriptor in creator.params.schema().items():
            schema[self.param_type_param_name(arg_name)] = create_choice_descriptor(
                self.param_type_param_name(arg_name),
                choices,
                "How {:s} values are to be sampled".format(arg_name),
                index,
                True,
                "fixed")
            self.__param_types["fixed"].append(arg_name)
            index += 10
            
        self.creator = creator
    
    def load(path): pass
    
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
    
    def param_type_param_name(self,arg_name):
        return "{:s}_param_type".format(arg_name)
    
    def values_list_param_name(self,arg_name):
        return "{:s}_values_list".format(arg_name)
        
    def range_min_param_name(self,arg_name):
        return "{:s}_range_min".format(arg_name)
                
    def range_max_param_name(self,arg_name):
        return "{:s}_range_max".format(arg_name)
        
    def range_to_number_param_name(self,arg_name):
        return "{:s}_to_number".format(arg_name)
        
    def range_from_number_param_name(self,arg_name):
        return "{:s}_from_number".format(arg_name)
    
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
        return self.get(self.values_list_param_name(arg_name))
    
    def get_values_range(self, arg_name): 
        assert self.get_param_type(arg_name) == "range"
        return (self.get(self.range_min_param_name(arg_name)),self.get(self.range_max_param_name(arg_name)))
        
    def get_to_number(self, arg_name):
        assert self.get_param_type(arg_name) == "range"
        return self.get(self.range_to_number_param_name(arg_name))
        
    def get_from_number(self, arg_name):
        assert self.get_param_type(arg_name) == "range"
        return self.get(self.range_from_number_param_name(arg_name))        
        
    def get_arg_values(self,include_fixed=False):
        """
        @rtype: List of tuples (arg_name, param_type, value(s)/range)
        """
        result = []
        for arg_name in self.arg_names():
            param_type = self.get_param_type(arg_name)
            if param_type == "fixed":
                if include_fixed:
                    result.append( (arg_name, param_type, self.creator.params.get(arg_name)) )
            elif param_type == "list":
                result.append( (arg_name, param_type, self.get_values_list(arg_name)) )
            else:
                assert (param_type == "range")
                result.append( (arg_name, param_type, self.get_values_range(arg_name)) )
        return result
    
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
                self.clear("num_samples")
                del self._Params__schema["num_samples"]
                
        # a creator parameter type was set (to fixed, list, or range)
        if self.__is_param_type(param_name):
            arg_name = self.__get_arg_name(param_name)
            param_type = self.get(param_name)
            old_param_type = self.get_param_type(arg_name)
            if param_type != old_param_type:
                # adjust map
                self.__param_types[old_param_type] = \
                    [x for x in self.__param_types[old_param_type] if not (x == arg_name)]
                self.__param_types[param_type].append(arg_name)
                
                # adjust dependent parammeters
                index = self._Params__schema[param_name].index
                values_list_param_name = self.values_list_param_name(arg_name)
                range_min_param_name = self.range_min_param_name(arg_name)
                range_max_param_name = self.range_max_param_name(arg_name)
                range_to_number_param_name = self.range_to_number_param_name(arg_name)
                range_from_number_param_name = self.range_from_number_param_name(arg_name)
                if param_type == "fixed":
                    # delete any list parameters
                    if values_list_param_name in self._Params__schema:
                        self.clear(values_list_param_name)
                        del self._Params__schema[values_list_param_name]
                    # delete any range parameters
                    if range_min_param_name in self._Params__schema:
                        self.clear(range_min_param_name)
                        del self._Params__schema[range_min_param_name]
                    if range_max_param_name in self._Params__schema:
                        self.clear(range_max_param_name)
                        del self._Params__schema[range_max_param_name]
                    if range_to_number_param_name in self._Params__schema:
                        self.clear(range_to_number_param_name)
                        del self._Params__schema[range_to_number_param_name]
                    if range_from_number_param_name in self._Params__schema:
                        self.clear(range_from_number_param_name)
                        del self._Params__schema[range_from_number_param_name]
                    
                elif param_type == "list":
                    # ensure list parameters
                    self._Params__schema[values_list_param_name] = ParamDescriptor(
                        values_list_param_name,
                        "Enumerated list of values for {:s}.".format(arg_name),
                        index + 1)
                    # delete any range parameters
                    if range_min_param_name in self._Params__schema:
                        self.clear(range_min_param_name)
                        del self._Params__schema[range_min_param_name]
                    if range_max_param_name in self._Params__schema:
                        self.clear(range_max_param_name)
                        del self._Params__schema[range_max_param_name]
                    if range_to_number_param_name in self._Params__schema:
                        self.clear(range_to_number_param_name)
                        del self._Params__schema[range_to_number_param_name]
                    if range_from_number_param_name in self._Params__schema:
                        self.clear(range_from_number_param_name)
                        del self._Params__schema[range_from_number_param_name]                        
                        
                else:
                    assert (param_type == "range")
                    # ensure range paramters
                    self._Params__schema[range_min_param_name] = ParamDescriptor(
                        range_min_param_name,
                        "Minimum value in range for {:s}.".format(arg_name),
                        index + 1)                    
                    self._Params__schema[range_max_param_name] = ParamDescriptor(
                        range_max_param_name,
                        "Maximum value in range for {:s}.".format(arg_name),
                        index + 2)
                    self._Params__schema[range_to_number_param_name] = ParamDescriptor(
                        range_to_number_param_name,
                        "Function to convert range endpoints for {:s} into numbers.".format(arg_name),
                        index + 3,
                        True,
                        lambda x: x)
                    self._Params__schema[range_from_number_param_name] = ParamDescriptor(
                        range_from_number_param_name,
                        "Function to convert numbers into values within the range for {:s}.".format(arg_name),
                        index + 4,
                        True,
                        lambda x: x)
                    # delete any list parameters
                    if values_list_param_name in self._Params__schema:
                        self.clear(values_list_param_name)
                        del self._Params__schema[values_list_param_name]                    
                    
    def __is_param_type(self,param_name): 
        """
        Returns true if param_name is of the form of "{:s}_param_type".format(arg_name).
        """
        return re.match('.+_param_type',param_name)
        
    def __get_arg_name(self,param_name): 
        """
        If self.__is_param_type(param_name), returns the arg_name.
        """
        assert self.__is_param_type(param_name)
        return re.match('(.+)_param_type',param_name).group(1)
        
    
class ComputationalStudyCreator(Creator):
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
        study_type = self.params.get("study_type")     
        if study_type == "lhs":
            num_samples = self.params.get("num_samples")
            assert (num_samples is not None)
            self.__lhs(num_samples)
        else :
            assert study_type == "full_factorial"
            self.__full_factorial()
                
    def __full_factorial(self): 
        # should only contain "list" arguments
        arg_values = self.params.get_arg_values()
        print("\n\nFull Factorial===============")
        print(arg_values)
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
            
        print(arg_names)
        print(current_points)
        self.__run_sub_creator(arg_names,current_points)
    
    def __lhs(self,num_samples): 
        # can contain "list" and "range" arguments              
        arg_values = self.params.get_arg_values()               
        print("\n\nLHS =========================")
        print(arg_values)
        lhs_design = lhs(len(arg_values), samples=num_samples)
        assert (len(lhs_design) == num_samples)
        assert (len(lhs_design[0]) == len(arg_values))
        # now apply uniform distribution
        points = []
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
                to_number = self.params.get_to_number(arg[0])
                from_number = self.params.get_from_number(arg[0])
                convert_function = lambda x: from_number(uniform(to_number(arg[2][0]),to_number(arg[2][1])).ppf(x))
                
            point_index = 0
            for lhs_point in lhs_design:
                points[point_index].append(convert_function(lhs_point[arg_index]))
                point_index += 1
            arg_index += 1
            
        assert (len(points) == num_samples)
        print(arg_names)
        print(points)
        self.__run_sub_creator(arg_names,points)        
    
    def __run_sub_creator(self,arg_names,arg_values): 
        for point in arg_values:
            assert(len(arg_names) == len(point))
            index = 0
            for value in point:
                self.params.creator.params.set(arg_names[index],value)
                index += 1
            self.params.creator.create()

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
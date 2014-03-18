
from CreatorBase import Params, ParamDescriptor, Creator, create_choice_descriptor

import re

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
        result = self.__param_types["fixed"]
        result.extend(self.__param_types["list"])
        result.extend(self.__param_types["range"])
        return result
    
    def param_type_param_name(self,arg_name):
        return "{:s}_param_type".format(arg_name)
    
    def values_list_param_name(self,arg_name):
        return "{:s}_values_list".format(arg_name)
        
    def range_min_param_name(self,arg_name):
        return "{:s}_range_min".format(arg_name)
                
    def range_max_param_name(self,arg_name):
        return "{:s}_range_max".format(arg_name)
    
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
        return self.get(values_list_param_name)
    
    def get_values_range(self, arg_name): 
        assert self.get_param_type(arg_name) == "range"
        return (self.get(range_min_param_name),self.get(range_max_param_name))
    
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
                        
    def create(self): pass
        # remove if necessary, and then make, out_dir
        
        # get the study_type and related parameters
        
        # delegate work to the study_type-specific create method
        
    def __full_factorial(self): pass
    
    def __lhs(self): pass
    
    def __run_sub_creator(self,arg_values): pass

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])

from abc import abstractmethod

import copy
import datetime as dt
import json
import marshal
import numpy
import os
import re

def base_path():
    """
    Returns the base path of the omf-glm-generator project.
    
    @rtype: string
    @return: base path of the omf-glm-generator
    """
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    
class ParamDescriptor:
    """
    Information describing a paramter.
    """
    def __init__(self, 
                 name, 
                 description, 
                 index, 
                 required=True, 
                 default_value=None, 
                 parser=None,
                 suggested_values=None):
        """
        Create a new ParamDescriptor
        
        @type name: string
        @param name: The parameter's name.
        @type description: string
        @param description: The parameter's description.
        @type index: int
        @param index: Index of this descriptor in a given set of descriptors.
        @type required: boolean
        @param required: Whether or not the user is required to provide this parameter.
        @type default_value: the parameter's type, or convertible by parser
        @param default_value: A default value for this parameter.
        @type parser: functor
        @param parser: Function for processing parameter values into standard form.
        @type suggested_values: list or functor
        @param suggested_values: List or function for generating list of suggested values.
        """
        self.name = name
        self.description = description
        self.index = index
        self.required = required
        self.default_value = default_value
        if (default_value is not None) and (parser is not None):
            self.default_value = parser(default_value)
        self.parser = parser
        self.suggested_values = suggested_values # used for generating templates
        
    def __str__(self): 
        required_str = ('required' if self.required else 'optional')
        default_value_str = ("\n    default_value: {:s}".format(str(self.default_value)) if self.default_value is not None else "")
        return '{:s} - {:s}\n    {:s}{:s}'.format(self.name,required_str,self.description,default_value_str)
        
def to_timedelta(td): 
    """
    Tries to convert td to a real datetime.timedelta, rounded to the 
    nearest second. Raises a RuntimeError if not successful.
    """
    result = None
    try:
        if type(td) in [type(dt.timedelta()), type(numpy.timedelta64())]:
            result = td
        else:
            result = pandas.to_timedelta(td)    
    except:
        try:
            m = re.match('([0-9]{2}):([0-9]{2}):([0-9]{2}):([0-9]{2})',td)
            result = dt.timedelta(days=int(m.group(1)),
                                  hours=int(m.group(2)),
                                  minutes=int(m.group(3)),
                                  seconds=int(m.group(4)))
        except:
            raise RuntimeError("Could not convert {:s} to datetime.timedelta.".format(td))
    # round to nearest second
    result = dt.timedelta(seconds=round(result.total_seconds()))
    return result            
        
def create_choice_descriptor(name,
                             choices,
                             description_prefix,
                             index,
                             required=True,
                             default_value=None):
    """
    Helper method for describing parameters whose values should be chosen from a list.
    
    @type name: string
    @param name: The parameter's name.
    @type choices: list
    @param choices: List of valid choices for the parameter value.
    @type description_prefix: string
    @param description_prefix: String to be pre-pended to the choice list. Composite 
        string will be the parameter's description.
    @type index: int
    @param index: Index of this descriptor in a given set of descriptors. Used to order 
        items for display purposes.
    @type required: boolean
    @param required: Whether or not the user is required to provide this parameter.
    @type default_value: the parameter's type
    @param default_value: A default value for this parameter, must be in choices.
    
    @rtype: ParamDescriptor
    """
    return  ParamDescriptor(name,
                            "{:s} {:s}.".format(description_prefix,print_choice_list(choices)),
                            0,
                            required,
                            default_value,
                            lambda x: x if x in choices else None,
                            choices)

class Params(dict):
    """
    Base class for dictionary-based params with json serialization.
    """
    
    @abstractmethod
    def get_class_name(self): pass    
   
    def __init__(self, schema, *arg, **kw):
        """
        Initialize a Params object with values.
        
        @type values: dict of param_name, param_value
        @param values: User's parameter values.
        """
        self.__schema = schema
        super(Params, self).__init__(*arg,**kw)
        
    def __str__(self):
        result = 'Values:\n\n'
        for pair in self.__sorted_values(): 
            result += "{:s}: {:s}\n".format(pair[0],str(pair[1]))
        result += '\nDescriptors:\n\n'
        for descriptor in self.__sorted_descriptors():
            result += "{:s}\n\n".format(str(descriptor))
        return result
        
    def schema(self):
        """
        Returns a deep copy of the schema. (A Params schema cannot be modified, but others 
        may need to inspect it.)
        
        @rtype: dict of ParamDescriptors
        @return: Deep copy of this Params object's schema.
        """
        return copy.deepcopy(self.__schema)
    
    def __getitem__(self, param_name):
        if param_name in self:
            return super(Params, self).__getitem__(param_name)
        elif param_name in self.__schema:
            descriptor = self.__schema[param_name]
            return descriptor.default_value
        return None      

    def get(self, param_name):
        # do not use derived method -- use code in __getitem__
        return self.__getitem__(param_name)    
              
    def __setitem__(self, param_name, param_value):
        if param_name in self.__schema:
            descriptor = self.__schema[param_name]
            if descriptor.parser is not None:
                super(Params, self).__setitem__(param_name, descriptor.parser(param_value))
            else:
                super(Params, self).__setitem__(param_name, param_value)
            self.__refresh_schema(param_name)
        else:
            raise RuntimeError("{:s} is not a valid parameter.".format(param_name))
 
    def to_json_dict(self):
        d = dict(self.items())
        d["class_name"] = self.get_class_name()    
        return d    
 
    def to_json(self): 
        return json.dumps(self.to_json_dict(), 
                          cls=ParamsEncoder,
                          sort_keys=True,
                          indent=4,
                          separators=(',', ': '))
  
    def save(self, path): 
        f = open(path,'w')
        f.write(self.to_json())
        f.close()
  
    def json_template(self): pass
  
    def save_template(self, path): pass
  
    def valid(self): 
        for param_name, descriptor in self.__schema.items():
            if descriptor.required:
                if self.get(param_name) is None:
                    return False
        return True
    
    def __nonzero__(self): 
        return self.valid()
        
    def __sorted_values(self): 
        return sorted(self.items(), key=lambda pair: self.__schema[pair[0]].index)
    
    def __sorted_descriptors(self): 
        return sorted(self.__schema.values(), key=lambda descriptor: descriptor.index)  
        
    def __refresh_schema(self,param_name):
        return
        
class Creator:
    """
    Base class for classes that create one or more simulations in separate run folders.
    """
    @abstractmethod
    def get_class_name(self): pass    
    
    def __init__(self, out_dir, params, resources_dir = None):
        self.out_dir = os.path.realpath(out_dir)
        self.params = params
        self.resources_dir = resources_dir
        if not self.params.valid():
            raise RuntimeError("Cannot create glm files with invalid parameters:\n{:s}".format(self.params))
        
    @abstractmethod
    def create(self): pass
    
    def to_json_dict(self): 
        return {"class_name": self.get_class_name(),
                "out_dir": self.out_dir,
                "params": self.params.to_json_dict(),
                "resources_dir": self.resources_dir}

########################################
# Internal Helper Functions and Classes
########################################
    
def print_choice_list(choices):
    """
    @type choices: list
    @param choices: List of choices. Each must be printable using "{:s}".format(x).
    @rtype: string
    @return
    """
    str = "('{:s}'".format(choices[0])
    for x in choices[1:]:
        str = "{:s}|'{:s}'".format(str,x)
    str = "{:s})".format(str)
    return str    
    
def installed_sub_templates():
    result = []
    feeder_path = os.path.realpath(base_path() + "/data/Templates/")
    for subdir, dirs, files in os.walk(feeder_path):
        for file in files:
            result.append(file)
    return result    
    
def to_walltime(dt):
    """
    Method to convert a timedelta object into a walltime string for use by submit scripts.
    
    @type dt: timedelta
    @param dt: Walltime parameter in timedelta format.
    @rtype: string
    @return: dt converted to "DD:HH:MM:SS"
    """
    n_days = dt.days
    n_hours = dt.seconds // 3600
    n_mins = (dt.seconds // 60 ) % 60
    n_secs = dt.seconds % 60
    return "{:02d}:{:02d}:{:02d}:{:02d}".format(n_days,n_hours,n_mins,n_secs)
    
class ParamsEncoder(json.JSONEncoder):
    """
    Json encoding for all possible Params types. May need to be extended when
    a new class is derived from Params.
    """
    def default(self, obj):
        if isinstance(obj, dt.timedelta):
            # serialize dt.timedelta as string that can be parsed
            return to_walltime(obj)
        return json.JSONEncoder.default(self,obj)
     

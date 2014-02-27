
from abc import abstractmethod

class ParamDescriptor: pass
    """
    Information describing a paramter.
    """
    def __init__(self, name, description, index, required=True, default_value=None, parser=None):
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
        """
        self.name = name
        self.description = description
        self.required = required
        self.default_value = default_value
        if (default_value is not None) and (parser is not None):
            self.default_value = parser(default_value)
        self.parser = parser
        
    def __str__(self): 
        required_str = ('required' if self.required else 'optional')
        default_value_str = (print('\n    default_value: ',default_value) if default_value is not None else '')
        return '{:s} - {:s}\n    {:s}{:s}'.format(name,required_str,description,default_value_str)
        

class Params:
    """
    Base class for dictionary-based params with json serialization.
    """
    
    __schema = {}
    """
    @ivar: dict of ParamDescriptors keyed off of name
    """
    
    def __init__(self, values = {}):
        """
        Initialize a Params object with values.
        
        @type values: dict of param_name, param_value
        @param values: User's parameter values.
        """
        self.__values = {}
        for name, value in values.item():
            self.set(name,value)
        
    def __str__(self):
        result = 'Values:\n\n'
        for pair in self.__sorted_values(): 
            result += print(pair[0],': ',pair[1],'\n')
        result += '\nDescriptors:\n\n'
        for descriptor in self.__sorted_descriptors():
            result += print(descriptor,'\n\n')
        return result
    
    def get(self, param_name, return_default=False): 
        if param_name in self.__values:
            return self.__values[param_name]
        elif return_default and (param_name in self.__schema):
            descriptor = self.__schema[param_name]
            return descriptor.default_value
        return None            
  
    def set(self, param_name, param_value):
        if param_name in self.__schema:
            descriptor = self.__schema[param_name]
            if descriptor.parser is not None:
                self.__values[param_name] = descriptor.parser(param_value)
            else:
                self.__values[param_name] = param_value            
        else:
            raise RuntimeError("{:s} is not a valid parameter.".format(param_name))
    
    def clear(self, param_name): 
        if param_name in self.__values:
            del self.__values[param_name]
    
    def __getattr__(self, param_name): 
        return self.get(param_name)
        
    def __setattr__(self, param_name, param_value):
        self.set(param_name,param_value)
        
    def __delattr__(self, param_name):
        self.clear(param_name)
  
    def to_json(self): pass
  
    def save(self, path): pass
  
    def json_template(self): pass
  
    def save_template(self, path): pass
  
    @abstractmethod
    def load(path):
  
    def valid(self): 
        for name, descriptor in self.__schema:
            if descriptor.required:
                return False if name not in self.__values
        return True
    
    def __nonzero__(self): 
        return self.valid()
        
    def __sorted_values: 
        return sorted(self.__values.items(), key=lambda pair: self.__schema[pair[0]].index)
    
    def __sorted_descriptors: 
        return sorted(self.__schema.values(), key=lambda descriptor: descriptor.index)  

class Creator: pass

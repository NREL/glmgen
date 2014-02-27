from abc import abstractmethod

class Params: pass
    """
    Base class for dictionary-based params with json serialization.
    """
    # save to json
    # save json template
    # load from json
    # parameter documentation
    #   - description  
    #   - required or not
    #   - default value
    #   - parsing method
    # valid?
    
    __schema = {}
    """
    @ivar: Dict of parameter descriptors of the form 
           {param_name = [description, required, default value, parsing method]}.
    """
    
    def __init__(self, values = {}): pass
        """
        Initialize a Params object with values.
        
        @type values: dict of param_name, param_value
        @param values: User's parameter values.
        """
        
        # loop through values and keep the ones that fit the schema
        self.__values = {}
        
    def __str__(self): pass
  
    def get(self, param_name): pass
  
    def set(self, param_name, param_value): pass
    
    def clear(self, param_name): pass
    
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
    def load(self, path):
  
    def valid(self): pass
    
    def __nonzero__(self): 
        return self.valid()
  
  

class Creator: pass


from CreatorBase import Params, ParamDescriptor, Creator, create_choice_descriptor

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
    
    def load(path): pass
    
    def _Params__refresh_schema(self): 
        study_type = self.get("study_type")
        if study_type == "lhs":
            if "num_samples" not in self._Params__schema:
                index = len(self._Params__schema)
                self._Params__schema["num_samples"] = ParamDescriptor(
                    "num_samples",
                    "Number of samples to create for the study.",
                    index,
                    True,
                    None,
                    lambda x: int(x) if int(x) > 0 else None)
        elif "num_samples" in self._Params__schema:
            self.clear("num_samples")
            del self._Params__schema["num_samples"]
    
class ComputationalStudyCreator(Creator):
 
    def __init__(self, out_dir, params, resources_dir = None): pass

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
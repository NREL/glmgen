import Params from CreatorBase
import Creator from CreatorBase

class ComputationalCaseParams(Params): pass
    def __init__(self): pass
        # base_feeder - required, convertible to path
        # sim_duration - defaults to 1h, convertible to datetime.timedelta
        # sim_timestep - defaults to 1min, convertible to datetime.timedelta
        # technologies - defaults to baseline (0), list of integers

    def base_feeder(self): pass
        "Returns the real path to the base feeder."
  
    def sim_duration(self): pass
        "Returns the datetime.timedelta for the simulation duration."
        
    def sim_timestep(self): pass
        "Returns the datetime.timedelta for the simulation timestep."
        
    def technologies(self): pass
        "HERE -- one or list of technology packages to apply."
        
    # def io_intensity(): pass
    
    

class ComputationalCaseCreator(Creator): pass

def main(argv): pass
  # print params template json file
  # run creator on given params json file

if __name__ == "__main__":
    main(sys.argv[1:])
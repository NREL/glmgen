
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator, installed_feeders
from ComputationalStudyCreator import ComputationalStudyParams, ComputationalStudyCreator
import CreatorFactory

import datetime
import math
import os

def basic_case_creator():
    params = ComputationalCaseParams()
    params["base_feeder"] = "R1-12.47-2.glm"
    params["sub_template"] = "run_script.sub.template"
    out_dir = "./test_results"
    return ComputationalCaseCreator(out_dir,params)

def test_study_type_refresh():
    params = ComputationalStudyParams(basic_case_creator())
    params["study_type"] = "lhs"
    params["num_samples"] = 100
    assert (params["study_type"] == "lhs")
    assert (params["num_samples"] == 100)
    params["study_type"] = "full_factorial"
    assert (params["num_samples"] is None)
    p = "./test_results/study_type_refresh.json"
    params.save(p)
    
def test_valid_params():
    params = ComputationalStudyParams(basic_case_creator())
    # have to set study_type
    assert not params.valid()
    params["study_type"] = "full_factorial"
    # trivial one-point study
    assert params.valid()
    params[params.param_name("base_feeder")] = ["R1-12.47-1.glm","R1-12.47-2.glm","R1-12.47-3.glm"]
    assert (params.get_param_type("base_feeder") == "list")
    assert params.valid()
    params[params.param_name("sim_duration")] = (datetime.timedelta(hours=1),datetime.timedelta(days=30))
    assert (params.get_param_type("sim_duration") == "range")
    # cannot have range parameters with study_type full_factorial
    assert not params.valid()
    params["study_type"] = "lhs"
    params["num_samples"] = 24
    assert params.valid()
    p = "./test_results/valid_params.json"
    params.save(p)
    
def test_full_factorial():
    params = ComputationalStudyParams(basic_case_creator())
    params["study_type"] = "full_factorial"
    params[params.param_name("base_feeder")] = ["R1-12.47-1.glm","R1-12.47-2.glm"]
    assert (params.get_param_type("base_feeder") == "list")
    params[params.param_name("sim_duration")] = [datetime.timedelta(hours=1),datetime.timedelta(hours=24)]
    assert (params.get_param_type("sim_duration") == "list")
    p = "./test_results/full_factorial.json"
    params.save(p)    
    out_dir = os.path.realpath("./test_results/full_factorial")
    if not os.path.exists(os.path.dirname(out_dir)):
        os.mkdir(os.path.dirname(out_dir))
    creator = ComputationalStudyCreator(out_dir,params)
    creator.create()
    for subdir, dirs, files in os.walk(out_dir):
        assert(len(dirs) == 4) # four cases should be generated
        break

def test_lhs():
    params = ComputationalStudyParams(basic_case_creator())
    params["study_type"] = "lhs"
    params["num_samples"] = 10
    params[params.param_name("base_feeder")] = ["R1-12.47-1.glm","R1-12.47-2.glm","R1-12.47-3.glm"]
    assert (params.get_param_type("base_feeder") == "list")
    params[params.param_name("sim_duration")] = (datetime.timedelta(hours=1),datetime.timedelta(days=30))
    assert (params.get_param_type("sim_duration") == "range")
    p = "./test_results/lhs.json"
    params.save(p)    
    out_dir = os.path.realpath("./test_results/lhs")
    if not os.path.exists(os.path.dirname(out_dir)):
        os.mkdir(os.path.dirname(out_dir))
    creator = ComputationalStudyCreator(out_dir,params)
    creator.create()
    for subdir, dirs, files in os.walk(out_dir):
        assert(len(dirs) == 10) # ten samples were requested
        break
        
def test_lhs_from_json():
    params = ComputationalStudyParams(basic_case_creator())
    params["study_type"] = "lhs"
    params["num_samples"] = 5
    params[params.param_name("base_feeder")] = installed_feeders()
    params[params.param_name("sim_duration")] = (datetime.timedelta(minutes=5),datetime.timedelta(days=1))
    p = "./test_results/lhs_from_json.json"
    params.save(p)
    loaded_params = CreatorFactory.load(p)
    out_dir = "./test_results/lhs_from_json"
    if not os.path.exists(os.path.dirname(out_dir)):
        os.mkdir(os.path.dirname(out_dir))    
    creator = ComputationalStudyCreator(out_dir,loaded_params)
    creator.create()
    for subdir, dirs, files in os.walk(out_dir):
        assert(len(dirs) == 5) # five samples were requested
        break    
    print("--- ORIGINAL ---")
    print(params)
    print("--- LOADED ---")
    print(loaded_params)
    # assert(str(params) == str(loaded_params))        
        

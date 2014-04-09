
from CreatorBase import ParamDescriptor
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator
import CreatorFactory

import datetime
import os
import shutil

def test_params(): 
    params = ComputationalCaseParams()
    assert not params.valid()
    print(params)
    p = "test_results/params.json"
    params.save(p)
    
def test_schema_getter():
    params = ComputationalCaseParams()
    schema = params.schema()
    schema["base_feeder"] = ParamDescriptor(
        "base_feeder",
        "Adulterated copy of base_feeder",
        0,
        True)
    assert not (schema["base_feeder"].description == params.schema()["base_feeder"].description)
    params["base_feeder"] = "R1-12.47-1.glm"
    assert os.path.exists(params["base_feeder"])
    p = "test_results/schema_getter.json"
    params.save(p)
    
def test_create_case_simplest():
    params = ComputationalCaseParams()
    params["base_feeder"] = "R1-12.47-1.glm"
    out_dir = "test_results"
    creator = ComputationalCaseCreator(out_dir,params)
    creator.create()
    assert os.path.exists(out_dir)
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-1_1h/model.glm"))
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-1_1h/schedules"))
    p = "test_results/create_case_simplest.json"
    params.save(p)
    
def test_create_case_sub_script():
    params = ComputationalCaseParams()
    params["base_feeder"] = "R1-12.47-2.glm"
    params["sub_template"] = "run_script.sub.template"
    out_dir = "test_results"
    creator = ComputationalCaseCreator(out_dir,params)
    creator.create()
    assert os.path.exists(out_dir)
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-2_1h/model.glm"))
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-2_1h/run_script.sub"))
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-2_1h/schedules"))
    p = "test_results/create_case_sub_script.json"
    params.save(p)
    
def test_create_case_from_json():
    params = ComputationalCaseParams()
    params["base_feeder"] = "R5-12.47-5.glm"
    params["case_name"] = "R5-12.47-5_1d_FromJSON"
    params["sim_duration"] = datetime.timedelta(days=1)
    p = "test_results/create_case_from_json.json"
    params.save(p)
    loaded_params = CreatorFactory.load(p)
    out_dir = "test_results"
    creator = ComputationalCaseCreator(out_dir,loaded_params)
    creator.create()
    assert os.path.exists(out_dir)
    assert os.path.exists(os.path.realpath(out_dir + "/R5-12.47-5_1d_FromJSON/model.glm"))
    assert os.path.exists(os.path.realpath(out_dir + "/R5-12.47-5_1d_FromJSON/schedules"))
    print("--- ORIGINAL ---")
    print(params)
    print("--- LOADED ---")
    print(loaded_params)
    assert(str(params) == str(loaded_params))
    


from CreatorBase import ParamDescriptor
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator

import os
import shutil

def test_params(): 
    params = ComputationalCaseParams()
    assert not params.valid()
    print(params)
    
def test_schema_getter():
    params = ComputationalCaseParams()
    schema = params.schema()
    schema["base_feeder"] = ParamDescriptor(
        "base_feeder",
        "Adulterated copy of base_feeder",
        0,
        True)
    assert not (schema["base_feeder"].description == params.schema()["base_feeder"].description)
    params.set("base_feeder","R1-12.47-1.glm")
    assert os.path.exists(params.get("base_feeder"))
    
def test_create_case_simplest():
    params = ComputationalCaseParams()
    params.set("base_feeder","R1-12.47-1.glm")
    out_dir = "test_results"
    creator = ComputationalCaseCreator(out_dir,params)
    creator.create()
    assert os.path.exists(out_dir)
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-1_1h/model.glm"))
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-1_1h/schedules"))
    
def test_create_case_sub_script():
    params = ComputationalCaseParams()
    params.set("base_feeder","R1-12.47-2.glm")
    params.set("sub_template","run_script.sub.template")
    out_dir = "test_results"
    creator = ComputationalCaseCreator(out_dir,params)
    creator.create()
    assert os.path.exists(out_dir)
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-2_1h/model.glm"))
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-2_1h/run_script.sub"))
    assert os.path.exists(os.path.realpath(out_dir + "/R1-12.47-2_1h/schedules"))
    
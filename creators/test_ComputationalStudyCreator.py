
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator
from ComputationalStudyCreator import ComputationalStudyParams, ComputationalStudyCreator

import datetime

def basic_case_creator():
    params = ComputationalCaseParams()
    params.set("base_feeder","R1-12.47-2.glm")
    params.set("sub_template","run_script.sub.template")
    out_dir = "test_results"
    return ComputationalCaseCreator(out_dir,params)

def test_study_type_refresh():
    params = ComputationalStudyParams(basic_case_creator())
    params.set("study_type","lhs")
    params.set("num_samples",100)
    assert (params.get("study_type") == "lhs")
    assert (params.get("num_samples") == 100)
    params.set("study_type","full_factorial")
    assert (params.get("num_samples") is None)
    
def test_valid_params():
    params = ComputationalStudyParams(basic_case_creator())
    # have to set study_type
    assert not params.valid()
    params.set("study_type","full_factorial")
    # trivial one-point study
    assert params.valid()
    params.set(params.param_type_param_name("base_feeder"),"list")
    # need to specify list value
    assert not params.valid() 
    params.set(params.values_list_param_name("base_feeder"),["R1-12.47-1.glm","R1-12.47-2.glm","R1-12.47-3.glm"])
    assert params.valid()
    params.set(params.param_type_param_name("sim_duration"),"range")
    params.set(params.range_min_param_name("sim_duration"),datetime.timedelta(hours=1))
    params.set(params.range_max_param_name("sim_duration"),datetime.timedelta(days=30))
    # cannot have range parameters with study_type full_factorial
    assert not params.valid()
    params.set("study_type","lhs")
    params.set("num_samples",24)
    assert params.valid()
    

from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator
from ComputationalStudyCreator import ComputationalStudyParams, ComputationalStudyCreator

import datetime as dt

def test_all_technologies_one_feeder():
    # choose one feeder, short sim_duration. 
    # generate study (including submit script) for all technologies.
    case_params = ComputationalCaseParams()
    case_params["base_feeder"] = "R1-12.47-1.glm"
    case_params["sim_duration"] = dt.timedelta(minutes=15)
    case_creator = ComputationalCaseCreator("",case_params)
    study_params = ComputationalStudyParams(case_creator)
    study_params["study_type"] = "full_factorial"
    study_params[study_params.param_name("technology")] = case_params.schema()["technology"].suggested_values
    study_params["sub_template"] = "run_study.sub.template"
    study_params["time_per_job"] = dt.timedelta(minutes=(15/100.0)) # 9 s per job
    out_dir = "test_results/all_technologies_one_feeder"
    study_creator = ComputationalStudyCreator(out_dir,study_params)
    study_creator.create()
    
def test_sample_technologies_feeders(): pass
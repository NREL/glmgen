
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator
from ComputationalStudyCreator import ComputationalStudyParams, ComputationalStudyCreator

import datetime as dt

def test_PV():
    # one feeder, simulate 15 minutes
    # baseline (0) + solar combined (13)
    # TODO: investigate sim_timestep
    # TODO: have ComputationalStudy make the case names
    # TODO: write multiprocessing runner
    case_params = ComputationalCaseParams()
    case_params["base_feeder"] = "R1-12.47-1.glm"
    case_params["sim_duration"] = dt.timedelta(minutes=15)
    case_params["solar_penetration"] = 10.0
    case_creator = ComputationalCaseCreator("",case_params)
    study_params = ComputationalStudyParams(case_creator)
    study_params["study_type"] = "full_factorial"
    study_params[study_params.param_name("technology")] = [0,13]
    study_params["sub_template"] = "run_study.sub.template"
    study_params["time_per_job"] = dt.timedelta(minutes=(15/30.0)) # 30 s per job
    out_dir = "./test_results/PV"
    resources_dir = out_dir + "/resources"
    study_creator = ComputationalStudyCreator(out_dir,study_params,resources_dir)
    study_creator.create()

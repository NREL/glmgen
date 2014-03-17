
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator
from ComputationalStudyCreator import ComputationalStudyParams, ComputationalStudyCreator

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
    
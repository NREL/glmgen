
from ComputationalCaseCreator import ComputationalCaseParams, ComputationalCaseCreator

import os
import shutil

def test_params(): 
    params = ComputationalCaseParams()
    assert not params.valid()
    print(params)
    
def test_create_case_simplest():
    params = ComputationalCaseParams()
    params.set("base_feeder","R1-12.47-1.glm")
    out_dir = "test_results"
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    creator = ComputationalCaseCreator(out_dir,params)
    creator.create()
    assert os.path.exists(out_dir)
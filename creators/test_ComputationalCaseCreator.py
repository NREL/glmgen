
from ComputationalCaseCreator import ComputationalCaseParams

def test_params(): 
    params = ComputationalCaseParams()
    assert not params.valid()
    print(params)
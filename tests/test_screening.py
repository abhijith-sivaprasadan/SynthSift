import numpy as np
from synthsift.screening import workload_at_recall, evaluate_scores

def test_workload_recall():
    y=np.array([1,0,1,0]); s=np.array([.9,.8,.7,.1])
    x=workload_at_recall(y,s,1.0)
    assert x['screen_n']==3
    assert x['achieved_recall']==1.0

def test_confusion_shape():
    r=evaluate_scores([1,0,1,0],[.9,.2,.4,.8])
    assert r.confusion==[[1,1],[1,1]]

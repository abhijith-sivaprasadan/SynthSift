from synthsift.extraction import extract_country,extract_sample_size,extract_study_design

def test_extract_country():
    assert extract_country('A nationally representative sample in Ireland')=='Ireland'

def test_extract_sample_size():
    assert extract_sample_size('sample of homeowners in Ireland (n = 574)')==574

def test_extract_design():
    assert extract_study_design('using an agent-based modeling and simulation approach')=='agent_based_model'

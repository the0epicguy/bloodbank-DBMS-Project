from app.core.compatibility import compatible_groups

def test_o_negative_rbc_only_o_negative():
    assert compatible_groups("O-", "RBC") == ["O-"]

def test_ab_positive_rbc_accepts_all_groups():
    assert set(compatible_groups("AB+", "RBC")) == {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}

def test_plasma_mapping_from_project_plan():
    assert set(compatible_groups("O-", "PLASMA")) == {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"}

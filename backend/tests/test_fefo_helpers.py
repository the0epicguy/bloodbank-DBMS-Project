from app.core.compatibility import compatible_groups

def test_fefo_policy_is_expiry_first():
    # Service query order is expiry_date ASC, then bank_id and unit_id for deterministic ties.
    from pathlib import Path
    source_path = Path(__file__).resolve().parent.parent / "app" / "services" / "issue_service.py"
    source = source_path.read_text(encoding="utf-8")
    assert "order_by(BloodUnit.expiry_date.asc()" in source
    assert "with_for_update(skip_locked=True)" in source

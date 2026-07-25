from pathlib import Path
import importlib.util


def load_module():
    path = Path(__file__).parents[1] / "scripts" / "check_processed_privacy.py"
    spec = importlib.util.spec_from_file_location("privacy_audit", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_processed_data_has_no_direct_identifier_columns():
    module = load_module()
    root = Path(__file__).parents[1] / "data" / "processed"
    assert module.audit(root) == []

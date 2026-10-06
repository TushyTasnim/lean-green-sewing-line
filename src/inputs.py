"""Load the line input data: operations table and line parameters."""
from pathlib import Path

import pandas as pd
import yaml

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def parse_predecessors(cell: str | float) -> list[int]:
    """Turn a cell like '4;5' into [4, 5]; an empty cell (NaN) into []."""
    if pd.isna(cell):
        return []
    return [int(p) for p in cell.split(";")]


def load_operations(path: Path = DATA_DIR / "operations.csv") -> pd.DataFrame:
    """Read operations.csv, indexed by op_id, with predecessors as lists."""
    ops = pd.read_csv(path, dtype={"predecessors": str})
    ops["predecessors"] = ops["predecessors"].apply(parse_predecessors)
    return ops.set_index("op_id")


def load_parameters(path: Path = DATA_DIR / "parameters.yaml") -> dict:
    """Read parameters.yaml into a nested dictionary."""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_precedence(ops: pd.DataFrame) -> list[int]:
    """Check op_ids are unique, predecessors exist, and there are no cycles.

    Returns op_ids in a valid processing order. Raises ValueError if invalid.
    """
    if ops.index.duplicated().any():
        raise ValueError(f"Duplicate op_ids: {list(ops.index[ops.index.duplicated()])}")

    known = set(ops.index)
    for op_id, preds in ops["predecessors"].items():
        missing = [p for p in preds if p not in known]
        if missing:
            raise ValueError(f"Operation {op_id} has unknown predecessors {missing}")

    order: list[int] = []
    remaining = {op_id: set(preds) for op_id, preds in ops["predecessors"].items()}
    while remaining:
        ready = sorted(op for op, preds in remaining.items() if preds <= set(order))
        if not ready:
            raise ValueError(f"Cycle: operations stuck in or behind a loop: {sorted(remaining)}")
        for op in ready:
            order.append(op)
            del remaining[op]
    return order
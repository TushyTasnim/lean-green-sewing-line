"""Line balancing: takt time, operators per operation, bottleneck, efficiency."""
import numpy as np
import pandas as pd


def takt_time(shift_min: float, target_pcs: float) -> float:
    """Takt time (min/pc) = available time / required output."""
    return shift_min / target_pcs


def theoretical_operators(ops: pd.DataFrame, takt: float) -> pd.Series:
    """Operators needed per operation = SMV / takt (fractional, not rounded)."""
    return (ops["smv_min"] / takt).rename("theoretical_ops")


def allocate_one_each(ops: pd.DataFrame) -> pd.Series:
    """Scenario A: one operator at every operation."""
    return pd.Series(1, index=ops.index, name="operators")


def allocate_by_takt(theoretical: pd.Series) -> pd.Series:
    """Scenario B: round SMV/takt up to whole operators.

    Rounded to 6 decimals first, so float noise such as 7.000000000000001
    does not add an extra operator.
    """
    return np.ceil(theoretical.round(6)).astype(int).rename("operators")


def balance_summary(ops: pd.DataFrame, operators: pd.Series, shift_min: float) -> dict:
    """Bottleneck, output and line efficiency for one operator allocation."""
    station_cycle = ops["smv_min"] / operators          # min per pc at each station
    line_cycle = station_cycle.max()                    # slowest station paces the line
    is_bottleneck = station_cycle.round(6) == round(line_cycle, 6)
    output = shift_min / line_cycle
    efficiency = ops["smv_min"].sum() / (operators.sum() * line_cycle)
    return {
        "operators": int(operators.sum()),
        "bottleneck_ops": station_cycle[is_bottleneck].index.tolist(),
        "cycle_time_min": round(float(line_cycle), 3),
        "output_pcs_per_shift": int(round(output, 6)),
        "line_efficiency_pct": round(float(100 * efficiency), 1),
    }
"""Busy/idle energy model for sewing-machine motors: kWh and CO2 per garment."""


def shift_energy_kwh(n_machines: int, machine_busy_min: float, shift_min: float,
                     energy: dict, motor: str) -> float:
    """Electricity (kWh) used by all sewing machines in one shift.

    The motor draws running power while stitching (stitching_fraction of busy time)
    and its idle power for the rest of the shift. motor is "clutch" or "servo".
    """
    stitch_min = energy["stitching_fraction"] * machine_busy_min
    idle_min = n_machines * shift_min - stitch_min
    idle_kw = energy[f"{motor}_idle_power_kw"]
    return (energy["running_power_kw"] * stitch_min + idle_kw * idle_min) / 60


def co2_kg(kwh: float, energy: dict) -> float:
    """CO2 (kg) for a given electricity use, using the grid emission factor."""
    ef = energy["grid_ef_kg_co2_per_kwh"]
    if ef is None:
        raise ValueError("grid_ef_kg_co2_per_kwh is null in parameters.yaml - find a source first")
    return kwh * ef


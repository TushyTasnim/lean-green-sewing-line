"""Discrete-event simulation of the T-shirt sewing line with SimPy."""
import random
import statistics

import pandas as pd
import simpy


def simulate_line(ops: pd.DataFrame, operators: pd.Series, variability: float,
                  seed: int, sim_time: float = 480, buffer_size: int = 10,
                  warmup: float = 0.0) -> dict:
    """Run one shift of the line; return garments finished and busy minutes per operation."""
    rng = random.Random(seed)
    env = simpy.Environment()
    feeds = {p for preds in ops["predecessors"] for p in preds}
    last_ops = [op for op in ops.index if op not in feeds]
    out = {op: simpy.Store(env, capacity=buffer_size) for op in ops.index}
    busy = {op: 0.0 for op in ops.index}
    finished = []
    wip_samples = []

    def operator(op: int):
        smv = ops.at[op, "smv_min"]
        while True:
            for p in ops.at[op, "predecessors"]:      # collect every input part
                yield out[p].get()
            start = env.now
            yield env.timeout(smv * rng.uniform(1 - variability, 1 + variability))
            busy[op] += max(0.0, env.now - max(start, warmup))   # count only post-warm-up time
            if op in last_ops:
                finished.append(env.now)
            else:
                yield out[op].put(op)                  # blocked if rack is full

    def wip_monitor():
        while True:                                   # count pieces on all racks
            if env.now >= warmup:
                wip_samples.append(sum(len(store.items) for store in out.values()))
            yield env.timeout(1.0)                    # once per minute

    for op in ops.index:
        for _ in range(int(operators[op])):
            env.process(operator(op))
    env.process(wip_monitor())
    env.run(until=warmup + sim_time)
    return {"output": sum(1 for t in finished if t >= warmup), "busy_min": busy,
            "mean_wip": sum(wip_samples) / len(wip_samples),
            "racks_end": {op: len(store.items) for op, store in out.items()}}


T_95_DF29 = 2.045   # two-sided 95% t value, 29 degrees of freedom (n = 30)


def run_replications(ops: pd.DataFrame, operators: pd.Series, variability: float,
                     n_reps: int = 30, **kwargs) -> pd.DataFrame:
    """Run the line with seeds 1..n_reps; one row of results per replication."""
    machines = ops.index[ops["machine"] != "Manual"]   # op 10 has no motor
    paid_min = operators.sum() * kwargs.get("sim_time", 480)
    rows = []
    for seed in range(1, n_reps + 1):
        r = simulate_line(ops, operators, variability, seed, **kwargs)
        rows.append({"seed": seed, "output": r["output"], "mean_wip": r["mean_wip"],
                     "efficiency": sum(r["busy_min"].values()) / paid_min,
                     "machine_busy_min": sum(r["busy_min"][op] for op in machines)})
    return pd.DataFrame(rows)


def mean_ci95(values: list[float]) -> tuple[float, float]:
    """Mean and 95% confidence-interval half-width for exactly 30 replications."""
    if len(values) != 30:
        raise ValueError("t = 2.045 is only valid for n = 30 replications")
    half_width = T_95_DF29 * statistics.stdev(values) / len(values) ** 0.5
    return statistics.mean(values), half_width
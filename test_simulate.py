import asyncio
import numpy as np
from bridge_server import simulate_step, BatchCellState

async def test():
    # Construct a mock BatchCellState
    # genes must have length n_agents * 4908
    n_agents = 5
    batch = BatchCellState(
        genes=[0.1] * (n_agents * 4908),
        proteins=[0.1] * (n_agents * 4908),
        chromatin=[0.2] * (n_agents * 4908),
        ages=[1.0] * n_agents,
        contexts=[0.0] * (n_agents * 4908),
        positions=[0.5, 0.5] * n_agents,
        burdens=[0.0] * n_agents,
        vector='OSKM',
        potency=1.0
    )
    try:
        res = await simulate_step(batch)
        print("Success! Result returned successfully.")
    except Exception as e:
        print(f"Error during simulate_step: {type(e).__name__}: {e}")

asyncio.run(test())

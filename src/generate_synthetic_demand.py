"""
generate_synthetic_demand.py

Creates a synthetic passenger demand dataset for use in training ML models.
Based on a realistic set of GTFS-like route/stop/time/weekday combinations.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Set reproducibility
np.random.seed(42)

# Configurable synthetic parameters
ROUTES = [f"R{i:03d}" for i in range(1, 21)]     # 20 routes: R001 to R020
STOPS = [f"ST{i:03d}" for i in range(1, 51)]     # 50 stops: ST001 to ST050
HOURS = list(range(6, 22))                       # Service from 6AM to 9PM
WEEKDAYS = list(range(7))                        # 0=Monday, 6=Sunday

# Generate cartesian product of demand entries
data = []
for route_id in ROUTES:
    for stop_id in STOPS:
        for hour in HOURS:
            for weekday in WEEKDAYS:
                # Simulate demand with a Poisson distribution (busier in mornings/evenings)
                if 7 <= hour <= 9 or 16 <= hour <= 18:
                    base_demand = np.random.poisson(lam=35)
                elif 10 <= hour <= 15:
                    base_demand = np.random.poisson(lam=15)
                else:
                    base_demand = np.random.poisson(lam=5)

                passenger_count = int(np.clip(base_demand, 0, 100))
                data.append({
                    "route_id": route_id,
                    "stop_id": stop_id,
                    "hour": hour,
                    "weekday": weekday,
                    "passenger_count": passenger_count
                })

# Create DataFrame
df = pd.DataFrame(data)

# Output path
output_dir = Path("GHANA_AI_HACKATHON/data")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "synthetic_demand.csv"

# Save to CSV
df.to_csv(output_file, index=False)
print(f"✅ Synthetic demand data saved to: {output_file.resolve()}")
print(f"🧮 Rows generated: {len(df)}")

"""
simulate_demand.py

Generates synthetic passenger demand data based on GTFS structure.
This script can later be updated to receive actual demand data via API from the Flutter app.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load GTFS trip structure
gtfs_path = Path("../data/raw_gtfs")
stop_times = pd.read_csv(gtfs_path / "stop_times.txt")
trips = pd.read_csv(gtfs_path / "trips.txt")
calendar = pd.read_csv(gtfs_path / "calendar.txt")

# Merge trips and calendar to get weekday service info
trips = trips.merge(calendar, on="service_id")
stop_times = stop_times.merge(trips, on="trip_id")

# Extract hour from arrival_time
def parse_hour(time_str):
    try:
        hour = int(time_str.split(":")[0]) % 24
        return hour
    except:
        return np.nan

stop_times["hour"] = stop_times["arrival_time"].apply(parse_hour)
stop_times = stop_times.dropna(subset=["hour"])

# Generate synthetic demand
np.random.seed(42)

synthetic_data = stop_times[["route_id", "stop_id", "hour"]].copy()
synthetic_data["weekday"] = np.random.randint(0, 7, size=len(synthetic_data))  # Mon–Sun
synthetic_data["passenger_count"] = np.random.poisson(lam=20, size=len(synthetic_data))

# Optional: Cap extreme values
synthetic_data["passenger_count"] = synthetic_data["passenger_count"].clip(0, 100)

# Save the synthetic dataset
output_path = Path("../data/synthetic_demand.csv")
synthetic_data.to_csv(output_path, index=False)
print(f"Synthetic demand data saved to: {output_path}")

# Placeholder: This section will later be replaced or updated via Flutter API inputs
# Example:
# def update_demand_from_flutter(route_id, stop_id, hour, weekday, passengers):
#     # Append to or update the synthetic_demand.csv file
#     pass

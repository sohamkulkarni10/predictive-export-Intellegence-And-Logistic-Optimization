# Logistics_Costs

Precomputed ocean + port + container costs from **every Indian port**
to **destination-country ports**.

## Files
- `india_to_world_port_costs.csv` — main dataset used by the backend
- `cost_lookup.py` — finds cheapest India → country route
- `build_costs_dataset.py` — rebuild from `Logistics/*.csv`

```bash
python build_costs_dataset.py
```

Backend uses this folder for logistics output and net-profit paths.

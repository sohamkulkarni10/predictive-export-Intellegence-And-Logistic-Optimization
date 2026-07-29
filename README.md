# Export AI — Indian exporter decision desk

Paste **news** → automatic:
1. Top 3 country + commodity demand (next month)
2. Commodity price in **INR / quintal**
3. Best India port → foreign port + **net profit**
4. Container priority (e.g. 6 containers)
5. Groq AI explanation for every stage

## Folders

| Folder | Role |
|---|---|
| `Demand_prediction/` | Your demand model + `predict_top3_from_news.py` |
| `commodities/` | Your price model (`price_agent_tools.py`) |
| `Logistics/` | Ports / freight CSVs + `commodity_country_trade.csv` |
| `Container_prioritization/` | Container allocation |
| `backend/` | Flask API + SQLite (`export_ai.db`) |
| `frontend/` | React UI (login + Indian theme) |

## Setup

1. Put Groq key in `backend/.env`:
```
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

2. Train models once (if missing):
```bash
cd Demand_prediction
python train_model.py

cd ../backend
python train_price.py
```

3. Run:
```bash
# terminal 1
cd backend
pip install -r requirements.txt
python app.py

# terminal 2
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Login (demo)
- `exporter` / `india@123`
- `demo` / `demo@123`
- `admin` / `admin@123`

## How profit is calculated
```
Net profit = avg export sell price (trade CSV)
           - predicted India buy price (₹/quintal → USD/ton)
           - logistics cost (inland + port + container + ocean)
```

Logistics cost parts are stored in SQLite table `logistics_costs`.

## Demand agent (standalone)
```bash
cd Demand_prediction
python predict_top3_from_news.py
```

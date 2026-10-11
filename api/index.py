
import csv
import io
import json
import math
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).resolve().parent.parent / "telemetry.csv"

@app.post("/")
async def metrics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold_ms", 180))

    with open(DATA_FILE, newline="", encoding="utf-8-sig") as f:
        records = list(csv.DictReader(f))

    result = {}
    for region in regions:
        rows = [
            r for r in records
            if r["region"] == region
        ]
        if not rows:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0,
            }
            continue

        latencies = sorted(float(r["latency_ms"]) for r in rows)
        uptimes = [float(r["uptime"]) for r in rows]
        p95_index = max(0, math.ceil(0.95 * len(latencies)) - 1)

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": latencies[p95_index],
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(x > threshold for x in latencies),
        }

    return JSONResponse(result)

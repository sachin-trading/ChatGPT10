# api.py
import logging
import collections
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

from bot_service import bot_service
import config

# Setup logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("api")

app = FastAPI(title="Trading Bot API", description="API for controlling and monitoring the algorithmic trading bot.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StatusResponse(BaseModel):
    is_running: bool
    last_run_time: Optional[str]
    active_positions_count: int
    disabled_strategies: List[str]

class PositionResponse(BaseModel):
    strategy: str
    symbol: str
    direction: str
    quantity: int
    entry_price: float
    sl_price: float
    tp_price: float
    opened_at: str
    pnl: float

class StrategyResponse(BaseModel):
    name: str
    enabled: bool
    active_position: bool

class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str

@app.on_event("startup")
async def startup_event():
    LOG.info("Initializing bot service on API startup")
    bot_service.initialize()
    # bot_service.start() # Uncomment if you want the bot to start automatically

@app.get("/status", response_model=StatusResponse)
async def get_status():
    return bot_service.get_status()

@app.post("/start")
async def start_bot():
    bot_service.start()
    return {"message": "Bot started"}

@app.post("/stop")
async def stop_bot():
    bot_service.stop()
    return {"message": "Bot stopped"}

@app.get("/positions", response_model=List[PositionResponse])
async def get_positions():
    return bot_service.get_positions()

@app.get("/strategies", response_model=List[StrategyResponse])
async def get_strategies():
    return bot_service.get_strategies()

@app.post("/strategies/{name}/toggle")
async def toggle_strategy(name: str, enabled: bool):
    bot_service.toggle_strategy(name, enabled)
    return {"message": f"Strategy {name} {'enabled' if enabled else 'disabled'}"}

@app.get("/logs", response_model=List[str])
async def get_logs(limit: int = 100):
    try:
        # Efficiently read the last N lines without loading the whole file into memory
        with open(config.LOG_FILE, "r") as f:
            return list(collections.deque(f, maxlen=limit))
    except FileNotFoundError:
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

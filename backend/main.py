import logging
import time
from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger("uvicorn.error")


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from drone_algo import DroneLoader


class OptimizeRequest(BaseModel):
    capacities: list[int] = Field(
        ..., min_length=1, max_length=5, description="每架无人机的最大载重",
    )
    packages: list[int] = Field(
        ..., min_length=1, max_length=50, description="每个包裹的重量",
    )

    @model_validator(mode="after")
    def validate_positive_values(self):
        if any(value <= 0 for value in self.capacities):
            raise ValueError("无人机载重必须为正整数")
        if any(value <= 0 for value in self.packages):
            raise ValueError("包裹重量必须为正整数")
        return self


class DroneResultRow(BaseModel):
    drone: str
    capacity: int
    actual_load: int
    remaining: int
    utilization: str


class OptimizeResponse(BaseModel):
    max_total: int
    total_capacity: int
    package_total: int
    undelivered: int
    utilization: float
    best_load: list[int]
    capacities: list[int]
    packages: list[int]
    process: list[list[int]]
    result_rows: list[DroneResultRow]


app = FastAPI(
    title="Drone Logistics Optimizer API",
    version="1.0.0",
    description="FastAPI backend for the rural drone logistics optimization demo.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{elapsed_ms:.1f}ms"
    return response


@app.on_event("startup")
def on_startup():
    logger.info("Drone Logistics Optimizer API 已启动")


@app.get("/api/health", summary="健康检查")
def health_check():
    return {"status": "ok"}


@app.post("/api/optimize", response_model=OptimizeResponse, summary="装载优化")
def optimize_payload(request: OptimizeRequest):
    start = time.perf_counter()
    try:
        loader = DroneLoader()
        loader.optimize(request.packages, request.capacities)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"算法执行失败：{exc}") from exc

    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "优化完成: %d架无人机, %d个包裹, 最大装载=%d, 耗时=%.1fms",
        len(request.capacities), len(request.packages), loader.max_total, elapsed_ms,
    )

    total_capacity = sum(request.capacities)
    package_total = sum(request.packages)
    undelivered = package_total - loader.max_total
    utilization = 0.0 if total_capacity == 0 else round(loader.max_total / total_capacity, 4)

    result_rows = [
        DroneResultRow(
            drone=f"无人机{idx}",
            capacity=max_capacity,
            actual_load=actual_load,
            remaining=max_capacity - actual_load,
            utilization=f"{(0 if max_capacity == 0 else actual_load / max_capacity):.1%}",
        )
        for idx, (actual_load, max_capacity) in enumerate(
            zip(loader.best_load, request.capacities), start=1,
        )
    ]

    return OptimizeResponse(
        max_total=loader.max_total,
        total_capacity=total_capacity,
        package_total=package_total,
        undelivered=undelivered,
        utilization=utilization,
        best_load=loader.best_load,
        capacities=request.capacities,
        packages=request.packages,
        process=loader.process,
        result_rows=result_rows,
    )

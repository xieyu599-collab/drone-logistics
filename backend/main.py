from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from drone_algo import DroneLoader


class OptimizeRequest(BaseModel):
    capacities: list[int] = Field(..., min_length=1, max_length=5, description="Maximum payload per drone")
    packages: list[int] = Field(..., min_length=1, max_length=50, description="Package weights")

    @model_validator(mode="after")
    def validate_positive_values(self):
        if any(value <= 0 for value in self.capacities):
            raise ValueError("capacities must all be positive integers")
        if any(value <= 0 for value in self.packages):
            raise ValueError("packages must all be positive integers")
        return self


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
    result_rows: list[dict[str, str | int]]


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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/optimize", response_model=OptimizeResponse)
def optimize_payload(request: OptimizeRequest):
    try:
        loader = DroneLoader()
        loader.optimize(request.packages, request.capacities)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    total_capacity = sum(request.capacities)
    package_total = sum(request.packages)
    undelivered = package_total - loader.max_total
    utilization = 0 if total_capacity == 0 else loader.max_total / total_capacity
    result_rows = []

    for idx, (actual_load, max_capacity) in enumerate(zip(loader.best_load, request.capacities), start=1):
        result_rows.append(
            {
                "drone": f"无人机{idx}",
                "capacity": max_capacity,
                "actual_load": actual_load,
                "remaining": max_capacity - actual_load,
                "utilization": f"{(0 if max_capacity == 0 else actual_load / max_capacity):.1%}",
            }
        )

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

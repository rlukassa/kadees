from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic import ConfigDict
from typing import Optional, List

from ..models.risk_model import MaternalAgeRiskModel
from ..simulation.monte_carlo import (
    MeiosisMonteCarloSimulator,
    SimulationConfig,
)
from ..simulation.statistics import SimulationStatisticsAnalyzer
from ..models.gamete import GameteSex
from ..data.loader import DatasetLoader


app = FastAPI(
    title="Chromosome Aneuploidy Predictor API",
    description=(
        "Backend API untuk prediksi kelainan kromosom akibat kegagalan meiosis. "
        "Menggunakan simulasi Monte Carlo berbasis model probabilistik usia maternal. "
        "Semua response menggunakan konvensi penamaan camelCase."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

riskModel  = MaternalAgeRiskModel()
dataLoader = DatasetLoader()

class SimulationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    maternalAge: int = Field(
        ..., ge=15, le=49, alias="maternal_age",
        description="Usia ibu (15–49 tahun)",
        json_schema_extra={"example": 30},
    )
    nSimulations: int = Field(
        10_000, ge=100, le=100_000, alias="n_simulations",
        description="Jumlah iterasi Monte Carlo",
    )
    targetChromosome: int = Field(
        21, ge=1, le=23, alias="target_chromosome",
        description="Nomor kromosom fokus (default: 21)",
    )
    randomSeed: Optional[int] = Field(
        None, alias="random_seed",
        description="Seed RNG untuk reprodusibilitas",
    )


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Chromosome Aneuploidy API v2.0 is running", "namingConvention": "camelCase"}


@app.get("/api/risk/curve", tags=["Risk Model"])
async def getRiskCurve(
    ageMin: int = Query(15, ge=15, le=49, alias="age_min", description="Usia minimum kurva"),
    ageMax: int = Query(49, ge=16, le=49, alias="age_max", description="Usia maksimum kurva"),
):

    if ageMin >= ageMax:
        raise HTTPException(status_code=400, detail="ageMin harus lebih kecil dari ageMax.")
    curve = riskModel.getRiskCurve(ageRange=(ageMin, ageMax))
    return {"curve": curve, "totalPoints": len(curve)}


@app.get("/api/risk/compare", tags=["Risk Model"])
async def compareAges(
    ageA: int = Query(..., ge=15, le=49, alias="age_a", description="Usia pertama"),
    ageB: int = Query(..., ge=15, le=49, alias="age_b", description="Usia kedua"),
):
    comparison = riskModel.compareAges(ageA, ageB)
    return comparison


@app.get("/api/risk/{maternalAge}", tags=["Risk Model"])
async def getRiskProfile(maternalAge: int):
    if not (15 <= maternalAge <= 49):
        raise HTTPException(status_code=400, detail="Usia harus antara 15–49 tahun.")
    profile = riskModel.getRiskProfile(maternalAge)
    return profile.toDict()


@app.post("/api/simulate", tags=["Simulation"])
async def runSimulation(request: SimulationRequest):

    config = SimulationConfig(
        maternalAge=request.maternalAge,
        nSimulations=request.nSimulations,
        targetChromosome=request.targetChromosome,
        gameteSex=GameteSex.EGG,
        randomSeed=request.randomSeed,
    )
    simulator = MeiosisMonteCarloSimulator(config, riskModel)
    result    = simulator.run()
    resultDict = result.toDict()

    analyzer = SimulationStatisticsAnalyzer([resultDict["results"]])
    wilsonCI = analyzer.wilsonConfidenceInterval(
        successes=result.aneuploidCount,
        n=result.totalRuns,
        confidence=0.95,
    )
    compStats = analyzer.compareObservedVsModel(
        observed=result.observedRisk,
        model=result.modelRisk,
        n=result.totalRuns,
    )
    resultDict["results"]["wilsonCI"]          = wilsonCI.toDict()
    resultDict["results"]["modelValidation"]   = compStats

    return resultDict


@app.get("/api/simulate/sweep", tags=["Simulation"])
async def runAgeSweep(
    ageMin: int = Query(20, ge=15, le=49, alias="age_min", description="Usia awal sweep"),
    ageMax: int = Query(45, ge=16, le=49, alias="age_max", description="Usia akhir sweep"),
    nSim:   int = Query(1000, ge=100, le=10_000, alias="n_sim", description="Iterasi per usia"),
):
    if ageMin >= ageMax:
        raise HTTPException(status_code=400, detail="ageMin harus lebih kecil dari ageMax.")
    config = SimulationConfig(nSimulations=nSim, maternalAge=ageMin)
    simulator = MeiosisMonteCarloSimulator(config, riskModel)
    sweepResults = simulator.runAgeSweep(ageRange=(ageMin, ageMax))
    return {"sweep": sweepResults, "total_ages": len(sweepResults)}


@app.get("/api/stats/analyze", tags=["Statistics"])
async def analyzeAge(
    age:        int = Query(..., ge=15, le=49, description="Usia maternal yang dianalisis"),
    nSim:       int = Query(10_000, ge=1000, le=100_000, alias="n_sim", description="Jumlah iterasi"),
    baseline:   int = Query(25, ge=15, le=49, description="Usia baseline untuk Relative Risk"),
    confidence: float = Query(0.95, ge=0.90, le=0.99, description="Level kepercayaan CI (0.90/0.95/0.99)"),
):

    config    = SimulationConfig(maternalAge=age, nSimulations=nSim)
    simulator = MeiosisMonteCarloSimulator(config, riskModel)
    result    = simulator.run()

    analyzer  = SimulationStatisticsAnalyzer([result.toDict()["results"]])
    wilsonCI  = analyzer.wilsonConfidenceInterval(result.aneuploidCount, result.totalRuns, confidence)

    baselineProfile = riskModel.getRiskProfile(baseline)
    rr = analyzer.relativeRisk(result.observedRisk, baselineProfile.totalRisk)

    comparison = analyzer.compareObservedVsModel(result.observedRisk, result.modelRisk, result.totalRuns)

    return {
        "age":          age,
        "nSimulations": nSim,
        "aneuploidCount":    result.aneuploidCount,
        "observedRisk":      round(result.observedRisk, 6),
        "observedRiskPercent": round(result.observedRisk * 100, 4),
        "modelRisk":         round(result.modelRisk, 6),
        "wilsonCI":          wilsonCI.toDict(),
        "relativeRisk":      round(rr, 2),
        "baselineAge":       baseline,
        "modelValidation":   comparison,
        "executionTimeMs":   round(result.executionTimeMs, 2),
    }

@app.get("/api/data/maternal-age", tags=["Data"])
async def getMaternalAgeData(
    limit: Optional[int] = Query(None, ge=1, description="Limit baris yang dikembalikan"),
):
    try:
        rows  = dataLoader.loadMaternalAgeRows()
        total = len(rows)
        if limit is not None:
            rows = rows[:limit]
        return {"count": total, "rowsReturned": len(rows), "rows": rows}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/api/data/maternal-age/{patientId}", tags=["Data"])
async def getMaternalAgeRow(patientId: str):
    try:
        rows = dataLoader.loadMaternalAgeRows()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
    for r in rows:
        if r.get("patientId") == patientId:
            return r
    raise HTTPException(status_code=404, detail=f"patientId '{patientId}' tidak ditemukan.")


@app.get("/api/data/syndromes", tags=["Data"])
async def listSyndromeReference():
    try:
        syndromes = dataLoader.loadSyndromeReference()
        return {"count": len(syndromes), "syndromes": syndromes}
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


@app.get("/api/data/stats", tags=["Data"])
async def getDatasetStats():
    try:
        rows = dataLoader.loadMaternalAgeRows()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    total = len(rows)
    aneuploidCount = sum(1 for r in rows if r.get("aneuploidyDetected") == 1
                          or str(r.get("aneuploidyDetected")) == "1")

    ages = []
    for r in rows:
        try:
            ages.append(float(r.get("maternalAge", 0)))
        except (ValueError, TypeError):
            pass

    analyzer = SimulationStatisticsAnalyzer([])
    ageStats = analyzer.descriptiveStats(ages) if ages else {}

    return {
        "totalRecords":     total,
        "aneuploidCount":   aneuploidCount,
        "normalCount":      total - aneuploidCount,
        "aneuploidRate":    round(aneuploidCount / total, 6) if total else 0,
        "maternalAgeStats": ageStats,
    }

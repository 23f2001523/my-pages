from fastapi import APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware

router = APIRouter()

EMAIL = "23f2001523@ds.study.iitm.ac.in"


@router.get("/stats")
def stats(values: str = Query(...)):
    nums = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }

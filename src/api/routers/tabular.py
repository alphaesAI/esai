from typing import List

from fastapi import APIRouter

router = APIRouter()

@router.get("/tabular")
def tabular(file: str):
    pass

@router.post("/batchtabular")
def batchtabular(file: List[str]):
    pass

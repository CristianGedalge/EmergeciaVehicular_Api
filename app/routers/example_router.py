from fastapi import APIRouter

router = APIRouter()

@router.get("/ejemplo")
def ejemplo():
    return {"msg": "Ruta de ejemplo funcionando"}

from fastapi import Depends, HTTPException, status
from app.dependencies.auth import obtenerUsuarioActual
class RequireRole:
    """
    Dependencia para restringir acceso por roles.
    Uso: Depends(RequireRole(["admin", "superadmin"]))
    """
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, usuario: dict = Depends(obtenerUsuarioActual)):
        if usuario.get("rol") not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de estos roles: {self.allowed_roles}"
            )
        return usuario
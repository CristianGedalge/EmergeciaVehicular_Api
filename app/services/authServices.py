from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
import bcrypt

from app.models.usuario import Usuario, RolEnum
from app.models.taller import Taller
from app.models.mecanico import Mecanico
from app.schemas.auth import RegisterRequest, RegisterAdminRequest
from app.config.auth import crear_token, verificar_token, RESET_TOKEN_EXPIRE_MINUTES
from app.helpers.email import enviarEmail, generarEmailReset, FRONTEND_URL


def hashearPassword(password: str) -> str:
    # bcrypt requires bytes, we encode to utf-8, hash it, then decode to store as string
    salt = bcrypt.gensalt()
    pwd_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verificarPassword(password_plano: str, password_hash: str) -> bool:
    pwd_bytes = password_plano.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)


async def registrarUsuario(db: AsyncSession, datos: RegisterRequest):
    """Registrar un nuevo usuario con password hasheado."""
    # Verificar si el correo ya existe
    query = select(Usuario).where(Usuario.correo == datos.correo)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return None  # Correo ya registrado

    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        password=hashearPassword(datos.password),
        telefono=datos.telefono,
        rol=datos.rol,
        fcm_token=datos.fcm_token,
        url_img=datos.url_img
    )
    db.add(nuevo_usuario)
    await db.commit()
    await db.refresh(nuevo_usuario)
    return nuevo_usuario


async def autenticarUsuario(db: AsyncSession, correo: str, password: str):
    """Verificar credenciales y retornar token JWT con tallerId según rol."""
    query = select(Usuario).where(
        Usuario.correo == correo,
        Usuario.estado == True
    )
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()

    if not usuario or not verificarPassword(password, usuario.password):
        return None

    # Claims base del token
    claims = {
        "sub": str(usuario.id),
        "correo": usuario.correo,
        "rol": usuario.rol
    }

    # Buscar tallerId según el rol
    if usuario.rol == RolEnum.ADMIN:
        query_taller = select(Taller).where(
            Taller.admin_id == usuario.id,
            Taller.estado == True
        )
        result_taller = await db.execute(query_taller)
        taller = result_taller.scalar_one_or_none()
        if taller:
            claims["tallerId"] = taller.id

    elif usuario.rol == RolEnum.MECANICO:
        query_mec = select(Mecanico).where(
            Mecanico.usuario_id == usuario.id,
            Mecanico.estado == True
        )
        result_mec = await db.execute(query_mec)
        mecanico = result_mec.scalar_one_or_none()
        if mecanico:
            claims["tallerId"] = mecanico.taller_id
            claims["mecanicoId"] = mecanico.id

    token = crear_token(claims)
    return token


async def solicitarResetPassword(db: AsyncSession, correo: str) -> bool:
    """
    Genera un token de reset y envía email con el enlace.
    Retorna True si se envió, False si el correo no existe.
    """
    query = select(Usuario).where(Usuario.correo == correo, Usuario.estado == True)
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()

    if not usuario:
        return False

    # Generar token de reset con expiración corta
    reset_token = crear_token(
        data={"sub": str(usuario.id), "tipo": "reset"},
        expires_delta=timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    )

    # Construir URL de reset
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"

    # Enviar email
    html = generarEmailReset(usuario.nombre, reset_url)
    enviarEmail(usuario.correo, "Recuperar contraseña - Emergencia Vehicular", html)

    return True


async def resetearPassword(db: AsyncSession, token: str, nueva_password: str) -> bool:
    """
    Verifica el token de reset y actualiza la contraseña.
    Retorna True si se actualizó, False si falló.
    """
    # Verificar y decodificar token
    payload = verificar_token(token)

    # Validar que sea un token de reset
    if payload.get("tipo") != "reset":
        return False

    # Buscar usuario
    usuario_id = int(payload["sub"])
    query = select(Usuario).where(Usuario.id == usuario_id, Usuario.estado == True)
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()

    if not usuario:
        return False

    # Actualizar contraseña
    usuario.password = hashearPassword(nueva_password)
    await db.commit()
    return True


async def registrarAdmin(db: AsyncSession, datos: RegisterAdminRequest):
    """
    Registrar un admin + su taller en una sola transacción.
    Si el correo ya existe, retorna None.
    """
    # Verificar si el correo ya existe
    query = select(Usuario).where(Usuario.correo == datos.correo)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        return None

    # 1. Crear usuario con rol admin
    nuevo_usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo,
        password=hashearPassword(datos.password),
        telefono=datos.telefono,
        rol=RolEnum.ADMIN,
        fcm_token=datos.fcm_token,
        url_img=datos.url_img
    )
    db.add(nuevo_usuario)
    await db.flush()  # Obtener ID sin commit

    # 2. Crear taller vinculado al admin
    nuevo_taller = Taller(
        nombre=datos.taller.nombre,
        direccion=datos.taller.direccion,
        telefono=datos.taller.telefono,
        latitud=datos.taller.latitud,
        longitud=datos.taller.longitud,
        admin_id=nuevo_usuario.id
    )
    db.add(nuevo_taller)

    await db.commit()
    await db.refresh(nuevo_usuario)
    await db.refresh(nuevo_taller)

    # 3. Generar token JWT con datos del admin y taller
    token = crear_token({
        "sub": str(nuevo_usuario.id),
        "correo": nuevo_usuario.correo,
        "rol": nuevo_usuario.rol,
        "tallerId": nuevo_taller.id
    })

    return {"accessToken": token, "usuarioId": nuevo_usuario.id, "tallerId": nuevo_taller.id}


async def actualizarFcmToken(db: AsyncSession, usuario_id: int, fcm_token: str):
    """Actualiza el token FCM de un usuario."""
    query = select(Usuario).where(Usuario.id == usuario_id)
    result = await db.execute(query)
    usuario = result.scalar_one_or_none()
    
    if not usuario:
        return False
        
    usuario.fcm_token = fcm_token
    await db.commit()
    return True


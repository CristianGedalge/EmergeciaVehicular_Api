import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

def subirImagen(archivo) -> str:
    """
    Sube un archivo (de FastAPI) a Cloudinary y retorna la URL segura.
    Se organiza en la carpeta especificada.
    """
    try:
        resultado = cloudinary.uploader.upload(
            archivo, 
            folder="emergencia_vehicular/fotos",
            resource_type="auto"
        )
        return resultado.get("secure_url")
    except Exception as e:
        print(f"Error al subir a Cloudinary: {e}")
        return None

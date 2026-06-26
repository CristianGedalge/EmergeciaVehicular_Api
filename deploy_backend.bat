@echo off
SETLOCAL Enabledelayedexpansion

echo ===================================================
echo   DESPLIEGUE DEL BACKEND FASTAPI EN AWS (ECS FARGATE)
echo ===================================================
echo.

:: Verificar AWS CLI
aws --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] AWS CLI no esta instalado o no se encuentra en el PATH.
    pause
    exit /b 1
)

:: Verificar Docker
docker --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker no esta instalado o no se encuentra en ejecucion.
    echo Asegurate de que Docker Desktop este abierto.
    pause
    exit /b 1
)

:: Solicitar Variables de AWS
set /p AWS_ACCOUNT_ID="Introduce tu AWS Account ID (12 digitos): "
if "%AWS_ACCOUNT_ID%"=="" (
    echo [ERROR] El AWS Account ID es obligatorio.
    pause
    exit /b 1
)

set /p AWS_REGION="Introduce tu region de AWS (Por defecto: us-east-1): "
if "%AWS_REGION%"=="" (
    set AWS_REGION=us-east-1
)

set /p ECR_REPO="Introduce el nombre del Repositorio ECR (Por defecto: emergencia-vehicular-api): "
if "%ECR_REPO%"=="" (
    set ECR_REPO=emergencia-vehicular-api
)

set /p ECS_CLUSTER="Introduce el nombre del Cluster ECS (Por defecto: emergencia-vehicular-cluster): "
if "%ECS_CLUSTER%"=="" (
    set ECS_CLUSTER=emergencia-vehicular-cluster
)

set /p ECS_SERVICE="Introduce el nombre del Servicio ECS (Por defecto: emergencia-vehicular-service): "
if "%ECS_SERVICE%"=="" (
    set ECS_SERVICE=emergencia-vehicular-service
)

set ECR_URI=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO%

echo.
echo [INFO] Resumen de Configuracion:
echo - Region: %AWS_REGION%
echo - Repositorio ECR: %ECR_URI%
echo - Cluster ECS: %ECS_CLUSTER%
echo - Servicio ECS: %ECS_SERVICE%
echo.

:: Login en AWS ECR
echo [INFO] Iniciando sesion en AWS ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com

if %ERRORLEVEL% neq 0 (
    echo [ERROR] El inicio de sesion en ECR fallo. Verifica tus credenciales de AWS.
    pause
    exit /b 1
)
echo [OK] Sesion iniciada correctamente en ECR.

:: Construir la Imagen Docker
echo [INFO] Construyendo la imagen Docker '%ECR_REPO%:latest'...
docker build -t %ECR_REPO% .

if %ERRORLEVEL% neq 0 (
    echo [ERROR] La construccion de la imagen Docker fallo.
    pause
    exit /b 1
)
echo [OK] Imagen Docker construida con exito.

:: Etiquetar la Imagen
echo [INFO] Etiquetando la imagen para ECR...
docker tag %ECR_REPO%:latest %ECR_URI%:latest

if %ERRORLEVEL% neq 0 (
    echo [ERROR] No se pudo etiquetar la imagen.
    pause
    exit /b 1
)

:: Subir a ECR
echo [INFO] Subiendo la imagen a ECR (%ECR_URI%:latest)...
docker push %ECR_URI%:latest

if %ERRORLEVEL% neq 0 (
    echo [ERROR] La subida a ECR fallo.
    pause
    exit /b 1
)
echo [OK] Imagen subida exitosamente a AWS ECR.

:: Forzar nueva implementacion en ECS Fargate
echo [INFO] Forzando nueva implementacion en el Servicio ECS '%ECS_SERVICE%'...
aws ecs update-service --cluster %ECS_CLUSTER% --service %ECS_SERVICE% --force-new-deployment --region %AWS_REGION%

if %ERRORLEVEL% neq 0 (
    echo [WARNING] No se pudo actualizar el servicio ECS.
    echo Asegurate de que el cluster '%ECS_CLUSTER%' y el servicio '%ECS_SERVICE%' existan en AWS.
) else (
    echo [OK] Despliegue en ECS Fargate iniciado correctamente. Las tareas se actualizaran en minutos.
)

echo.
echo ===================================================
echo DESPLIEGUE DEL BACKEND COMPLETADO EXITOSAMENTE
echo ===================================================
pause

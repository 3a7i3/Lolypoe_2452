@echo off
REM Quick deployment script for Crypto AI Trading System (Windows)
REM Usage: deploy.bat [development|production] [rebuild]

setlocal enabledelayedexpansion

echo.
echo 🚀 Crypto AI Trading System - Quick Deploy
echo ==========================================

REM Check prerequisites
echo.
echo Checking prerequisites...

docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker not installed
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker Compose not installed
    pause
    exit /b 1
)

echo ✓ Docker installed
echo ✓ Docker Compose installed

REM Parse arguments
set ENVIRONMENT=development
set REBUILD=false

if not "%1"=="" set ENVIRONMENT=%1
if not "%2"=="" set REBUILD=%2

echo.
echo Deployment Settings:
echo Environment: %ENVIRONMENT%
echo Rebuild Images: %REBUILD%

REM Select compose file
set COMPOSE_FILE=docker-compose.yml
if "%ENVIRONMENT%"=="production" (
    set COMPOSE_FILE=docker-compose.prod.yml
    echo Using: !COMPOSE_FILE! (Production HA Setup)
) else (
    echo Using: !COMPOSE_FILE! (Development Setup)
)

REM Check environment file
if not exist ".env" (
    echo.
    echo ⚠️  Creating .env from template...
    
    if exist ".env.production" (
        copy .env.production .env >nul
        echo ✓ .env created
        echo ⚠️  Please edit .env and set secure passwords!
    ) else (
        echo ❌ .env.production template not found
        pause
        exit /b 1
    )
) else (
    echo ✓ .env file exists
)

REM Build or pull images
echo.
echo Setting up Docker images...

if "%REBUILD%"=="true" (
    echo Rebuilding images...
    docker-compose -f !COMPOSE_FILE! build --no-cache
) else (
    echo Building application image...
    docker-compose -f !COMPOSE_FILE! build --quiet
)

echo ✓ Images ready

REM Stop existing services
for /f %%i in ('docker-compose -f !COMPOSE_FILE! ps -q 2^>nul ^| find /c /v ""') do set count=%%i

if !count! gtr 0 (
    echo.
    echo Stopping existing services...
    docker-compose -f !COMPOSE_FILE! down
)

REM Start services
echo.
echo Starting services...
docker-compose -f !COMPOSE_FILE! up -d

REM Wait for services to be healthy
echo.
echo Waiting for services to be healthy...
echo (This may take 30-60 seconds)

timeout /t 10 /nobreak

echo.
echo Health Check:

for /l %%i in (1,1,30) do (
    docker-compose -f !COMPOSE_FILE! ps api 2>nul | find "healthy" >nul
    if !errorlevel! equ 0 (
        docker-compose -f !COMPOSE_FILE! ps postgres 2>nul | find "healthy" >nul
        if !errorlevel! equ 0 (
            echo ✓ All services healthy
            goto :healthy
        )
    )
    echo.
    timeout /t 2 /nobreak >nul
)

:healthy

REM Display service status
echo.
echo Service Status:
docker-compose -f !COMPOSE_FILE! ps

REM Display access information
echo.
echo 🎉 Deployment Complete!
echo.
echo Access Information:
echo.
echo API Server
echo   URL:              http://localhost:8000
echo   Health Check:     http://localhost:8000/health
echo   API Docs:         http://localhost:8000/docs
echo   ReDoc:            http://localhost:8000/redoc
echo.
echo Dashboard
echo   URL:              http://localhost:8050
echo.
echo Database
echo   Host:             localhost
echo   Port:             5432
echo   PgAdmin:          http://localhost:5050
echo.

if "%ENVIRONMENT%"=="production" (
    echo Monitoring (Production)
    echo   Prometheus:       http://localhost:9090
    echo   Grafana:          http://localhost:3000
    echo.
)

echo Redis
echo   URL:              redis://localhost:6379
echo.

REM Useful commands
echo Useful Commands:
echo.
echo View logs:
echo   docker-compose -f !COMPOSE_FILE! logs -f api
echo   docker-compose -f !COMPOSE_FILE! logs -f dashboard
echo.
echo Stop services:
echo   docker-compose -f !COMPOSE_FILE! down
echo.
echo View resource usage:
echo   docker stats
echo.
echo Next Steps:
echo 1. Access dashboard at http://localhost:8050
echo 2. Check API docs at http://localhost:8000/docs
echo 3. Review logs: docker-compose logs -f
echo 4. For production, configure .env and SSL certificates
echo.
echo 📚 For more information, see DEPLOYMENT.md
echo.

pause

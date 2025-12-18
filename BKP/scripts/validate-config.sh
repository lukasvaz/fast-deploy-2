#!/bin/bash
# Script de validación de configuración del proyecto

set -e

echo "🔍 Validando configuración del Repositorio Académicos..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 - NO ENCONTRADO"
        ERRORS=$((ERRORS + 1))
    fi
}

# Function to check directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
    else
        echo -e "${YELLOW}⚠${NC} $1/ - NO ENCONTRADO"
        WARNINGS=$((WARNINGS + 1))
    fi
}

echo "📁 Verificando estructura de archivos..."
echo ""

echo "Archivos de configuración:"
check_file "manage.py"
check_file "requirements.txt"
check_file ".env.dev"
check_file ".gitignore"
check_file "Makefile"
echo ""

echo "Docker:"
check_file "Dockerfile"
check_file "Dockerfile.prod"
check_file "docker-compose.yml"
check_file "docker-compose.prod.yml"
check_file "dc-produccion.yml"
check_file "entrypoint.sh"
check_file "entrypoint.prod.sh"
echo ""

echo "Configuración Django:"
check_file "memoria/settings.py"
if [ -f "memoria/settings.prod.py" ]; then
    check_file "memoria/settings.prod.py"
else
    echo -e "${YELLOW}⚠${NC} memoria/settings.prod.py - NO ENCONTRADO (opcional si se usa env vars)"
fi
check_file "memoria/urls.py"
check_file "memoria/wsgi.py"
check_file "wsgi.py"
echo ""

echo "Apps Django:"
check_dir "api"
check_dir "etl"
check_dir "front"
check_dir "grados"
check_dir "persona"
check_dir "revision"
check_dir "universidad"
check_dir "users"
echo ""

echo "Directorios de recursos:"
check_dir "templates"
check_dir "staticfiles"
check_dir "uploads"
echo ""

echo "Template DCC:"
check_dir "basate en este proyecto/acad_micros"
check_file "basate en este proyecto/acad_micros/README.md"
check_file "basate en este proyecto/acad_micros/MIGRACION.md"
echo ""

echo "Documentación:"
check_file "README.md"
check_file "doc/README.md"
check_file "doc/ARCHITECTURE.md"
check_file "doc/DEPLOY.md"
check_file "doc/commands.MD"
echo ""

echo "🔧 Verificando sintaxis de archivos..."
echo ""

# Check Python syntax
if command -v python3 &> /dev/null; then
    if python3 -m py_compile manage.py 2>/dev/null; then
        echo -e "${GREEN}✓${NC} manage.py - Sintaxis Python OK"
    else
        echo -e "${RED}✗${NC} manage.py - Error de sintaxis Python"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC} Python3 no disponible, omitiendo validación de sintaxis"
    WARNINGS=$((WARNINGS + 1))
fi

# Check shell scripts
for script in entrypoint.sh entrypoint.prod.sh; do
    if bash -n "$script" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $script - Sintaxis Shell OK"
    else
        echo -e "${RED}✗${NC} $script - Error de sintaxis Shell"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check docker-compose syntax
if command -v docker &> /dev/null; then
    if docker compose config --quiet 2>/dev/null; then
        echo -e "${GREEN}✓${NC} docker-compose.yml - Sintaxis OK"
    else
        echo -e "${YELLOW}⚠${NC} docker-compose.yml - Advertencias (revisar)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker no disponible, omitiendo validación"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "📊 Resumen de validación:"
echo ""
echo "Errores críticos: $ERRORS"
echo "Advertencias: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Proyecto validado correctamente${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Revisar variables de entorno en .env"
    echo "  2. make docker-build  # Construir imagen"
    echo "  3. make docker-up     # Levantar servicios"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Se encontraron $ERRORS errores críticos${NC}"
    echo "Por favor, corrija los errores antes de continuar"
    echo ""
    exit 1
fi

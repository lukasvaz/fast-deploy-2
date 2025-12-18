#!/bin/bash
# Validation script for production deployment setup
# Run this before deploying to production

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔍 Validando configuración de producción..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

# Function to check and report
check_passed() {
    echo -e "${GREEN}✓${NC} $1"
    SUCCESS=$((SUCCESS + 1))
}

check_failed() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

echo "📋 Verificando archivos requeridos..."

# Check required files
if [ -f "docker-compose.prod.yml" ]; then
    check_passed "docker-compose.prod.yml existe"
else
    check_failed "docker-compose.prod.yml no encontrado"
fi

if [ -f "Dockerfile.prod" ]; then
    check_passed "Dockerfile.prod existe"
else
    check_failed "Dockerfile.prod no encontrado"
fi

if [ -f ".env.prod.sample" ]; then
    check_passed ".env.prod.sample existe"
else
    check_failed ".env.prod.sample no encontrado"
fi

if [ -f ".env.prod" ]; then
    check_passed ".env.prod existe"
    
    # Check for CHANGE_ME values
    if grep -q "CHANGE_ME" .env.prod 2>/dev/null; then
        check_warning ".env.prod contiene valores 'CHANGE_ME' - deben ser cambiados"
    else
        check_passed "Valores 'CHANGE_ME' actualizados en .env.prod"
    fi
    
    # Check for required variables
    required_vars=("DJANGO_SECRET_KEY" "POSTGRES_PASSWORD" "POSTGRES_DB" "POSTGRES_USER")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env.prod 2>/dev/null; then
            check_passed "Variable $var definida en .env.prod"
        else
            check_failed "Variable $var no encontrada en .env.prod"
        fi
    done
else
    check_warning ".env.prod no existe - debe crearse desde .env.prod.sample"
fi

echo ""
echo "🐳 Verificando Docker..."

# Check Docker
if command -v docker &> /dev/null; then
    check_passed "Docker está instalado"
    
    if docker info &> /dev/null; then
        check_passed "Docker daemon está corriendo"
    else
        check_failed "Docker daemon no está corriendo"
    fi
else
    check_failed "Docker no está instalado"
fi

# Check Docker Compose
if command -v docker compose &> /dev/null || command -v docker-compose &> /dev/null; then
    check_passed "Docker Compose está disponible"
    
    # Validate docker-compose.prod.yml
    if docker compose -f docker-compose.prod.yml config --quiet 2>/dev/null; then
        check_passed "docker-compose.prod.yml es válido"
    else
        check_failed "docker-compose.prod.yml tiene errores de sintaxis"
    fi
else
    check_failed "Docker Compose no está instalado"
fi

echo ""
echo "🌐 Verificando configuración de red..."

# Check for nginx network (if docker is available)
if command -v docker &> /dev/null && docker info &> /dev/null; then
    NGINX_NETWORK=$(grep "name: nginx-proxy" docker-compose.prod.yml 2>/dev/null)
    
    if [ -n "$NGINX_NETWORK" ]; then
        NETWORK_NAME=$(echo "$NGINX_NETWORK" | awk '{print $2}' | tr -d ' ')
        
        if docker network ls | grep -q "$NETWORK_NAME"; then
            check_passed "Red externa '$NETWORK_NAME' existe"
        else
            check_warning "Red externa '$NETWORK_NAME' no encontrada"
            echo "           Ejecute: make prod-detect-network para detectar la red correcta"
        fi
    fi
    
    # Try to detect nginx container
    if docker ps -a --format '{{.Names}}' | grep -q "nginx"; then
        NGINX_CONTAINER=$(docker ps -a --format '{{.Names}}' | grep "nginx" | head -1)
        check_passed "Contenedor nginx encontrado: $NGINX_CONTAINER"
        
        # Get nginx networks
        NGINX_NETWORKS=$(docker inspect "$NGINX_CONTAINER" --format '{{range $k,$v := .NetworkSettings.Networks}}{{println $k}}{{end}}' 2>/dev/null)
        if [ -n "$NGINX_NETWORKS" ]; then
            echo "           Redes de nginx: $NGINX_NETWORKS"
        fi
    else
        check_warning "No se encontró contenedor nginx - asegúrese de que existe"
    fi
fi

echo ""
echo "📦 Verificando archivos Python..."

# Check Python files syntax
if command -v python3 &> /dev/null; then
    check_passed "Python3 está disponible"
    
    if python3 -m py_compile memoria/settings/base.py 2>/dev/null; then
        check_passed "memoria/settings/base.py sintaxis OK"
    else
        check_failed "memoria/settings/base.py tiene errores de sintaxis"
    fi
    
    if python3 -m py_compile memoria/settings/prod.py 2>/dev/null; then
        check_passed "memoria/settings/prod.py sintaxis OK"
    else
        check_failed "memoria/settings/prod.py tiene errores de sintaxis"
    fi
    
    if python3 -m py_compile memoria/urls.py 2>/dev/null; then
        check_passed "memoria/urls.py sintaxis OK"
    else
        check_failed "memoria/urls.py tiene errores de sintaxis"
    fi
else
    check_warning "Python3 no disponible para validar sintaxis"
fi

echo ""
echo "📊 Resumen de validación"
echo "========================"
echo -e "${GREEN}Exitosos: $SUCCESS${NC}"
echo -e "${YELLOW}Advertencias: $WARNINGS${NC}"
echo -e "${RED}Errores: $ERRORS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Validación falló. Por favor corrija los errores antes de continuar.${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validación completada con advertencias. Revise antes de desplegar.${NC}"
    echo ""
    echo "Pasos sugeridos:"
    echo "  1. Revise las advertencias anteriores"
    echo "  2. Configure .env.prod con valores reales"
    echo "  3. Verifique la red de Nginx: make prod-detect-network"
    echo "  4. Ejecute: make prod-build"
    echo "  5. Ejecute: make prod-up"
    exit 0
else
    echo -e "${GREEN}✅ Validación exitosa! Puede proceder con el despliegue.${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. make prod-build    # Construir la imagen"
    echo "  2. make prod-up       # Levantar los servicios"
    echo "  3. make prod-migrate  # Ejecutar migraciones"
    echo "  4. make prod-logs     # Ver logs"
    exit 0
fi

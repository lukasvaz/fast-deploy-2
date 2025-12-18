# Guía de Despliegue - Repositorio Académicos

Esta guía explica cómo desplegar el proyecto en diferentes entornos.

## 📋 Prerrequisitos

### Para Desarrollo

- Docker y Docker Compose v2
- Git
- (Opcional) Python 3.12+ si quieres trabajar sin Docker

### Para Producción

- Servidor con Docker y Docker Compose
- Dominio configurado (opcional, para HTTPS)
- PostgreSQL (puede estar en Docker o servidor separado)
- Nginx (recomendado para proxy reverso)

## 🚀 Despliegue en Desarrollo

### Opción 1: Con Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
cd repositorio-acad-micos

# 2. Copiar variables de entorno
cp .env.dev .env

# 3. Editar .env si es necesario (opcional)
nano .env

# 4. Construir y levantar servicios
make docker-build
make docker-up

# O usar el comando de inicialización completa
make init-project

# 5. El proyecto estará disponible en http://localhost:8000
```

### Opción 2: Sin Docker

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
make install
# O: pip install -r requirements.txt

# 3. Configurar PostgreSQL
# Asegurarse de tener PostgreSQL corriendo
createdb memoria

# 4. Configurar variables de entorno
export DB_NAME=memoria
export DB_USER=memoriauser
export DB_PASSWORD=memoriapassword
export DB_HOST=localhost
export DB_PORT=5432

# 5. Ejecutar migraciones
make migrate

# 6. Cargar fixtures
make fixtures

# 7. Crear superusuario
make createsuperuser

# 8. Ejecutar servidor
make run
```

## 🏭 Despliegue en Producción

### 1. Preparar el Servidor

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Agregar usuario al grupo docker
sudo usermod -aG docker $USER

# Instalar Docker Compose v2
sudo apt install docker-compose-plugin

# Reiniciar sesión para aplicar cambios de grupo
```

### 2. Clonar y Configurar

```bash
# Clonar repositorio
git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
cd repositorio-acad-micos

# Crear directorio para archivos estáticos y media
sudo mkdir -p /home/instalar/static/acad_micros/
sudo mkdir -p /home/instalar/media/acad_micros/
sudo chown -R $USER:$USER /home/instalar/
```

### 3. Configurar Variables de Entorno

```bash
# Crear archivo .env.prod
cat > .env.prod << EOF
# Django Settings
DJANGO_SETTINGS_MODULE=memoria.settings.prod
DJANGO_SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=acad_micros
DB_USER=desarrollo
DB_PASSWORD=PASSWORD_SEGURO_AQUI
DB_HOST=postgresql
DB_PORT=5432

# CSRF
CSRF_TRUSTED_ORIGINS=https://tu-dominio.com,https://www.tu-dominio.com

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-password-de-app
EOF
```

### 4. Configurar Base de Datos Externa (Opcional)

Si usas PostgreSQL en servidor separado:

```bash
# En el servidor de PostgreSQL
sudo -u postgres psql

# Crear base de datos y usuario
CREATE DATABASE acad_micros;
CREATE USER desarrollo WITH PASSWORD 'PASSWORD_SEGURO_AQUI';
ALTER ROLE desarrollo SET client_encoding TO 'utf8';
ALTER ROLE desarrollo SET default_transaction_isolation TO 'read committed';
ALTER ROLE desarrollo SET timezone TO 'America/Santiago';
GRANT ALL PRIVILEGES ON DATABASE acad_micros TO desarrollo;
\q
```

### 5. Configurar Nginx como Proxy Reverso

```bash
# Crear red Docker para nginx-proxy
docker network create nginx-proxy

# Instalar Nginx
sudo apt install nginx

# Configurar sitio
sudo nano /etc/nginx/sites-available/acad_micros
```

Contenido del archivo de configuración de Nginx:

```nginx
server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    # Redirigir a HTTPS (descomentar cuando tengas certificado)
    # return 301 https://$server_name$request_uri;

    location /docencia/acad_micros/static/ {
        alias /home/instalar/static/acad_micros/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /docencia/acad_micros/media/ {
        alias /home/instalar/media/acad_micros/;
    }

    location /docencia/acad_micros/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header SCRIPT_NAME /docencia/acad_micros;
    }
}

# HTTPS configuration (descomentar cuando tengas certificado)
# server {
#     listen 443 ssl http2;
#     server_name tu-dominio.com www.tu-dominio.com;
#
#     ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
#
#     location /docencia/acad_micros/static/ {
#         alias /home/instalar/static/acad_micros/;
#         expires 30d;
#         add_header Cache-Control "public, immutable";
#     }
#
#     location /docencia/acad_micros/media/ {
#         alias /home/instalar/media/acad_micros/;
#     }
#
#     location /docencia/acad_micros/ {
#         proxy_pass http://localhost:8000/;
#         proxy_set_header Host $host;
#         proxy_set_header X-Real-IP $remote_addr;
#         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#         proxy_set_header X-Forwarded-Proto $scheme;
#         proxy_set_header SCRIPT_NAME /docencia/acad_micros;
#     }
# }
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/acad_micros /etc/nginx/sites-enabled/

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 6. Obtener Certificado SSL con Let's Encrypt (Opcional pero Recomendado)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obtener certificado
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# El certificado se renovará automáticamente
```

### 7. Desplegar Aplicación

```bash
# Construir imagen de producción
make prod-build

# Levantar servicios
make prod-up

# Verificar que los contenedores están corriendo
make status

# Ver logs
make prod-logs

# Ejecutar migraciones
make prod-migrate

# Recolectar archivos estáticos
make prod-collectstatic

# Crear superusuario (primera vez)
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 8. Configurar Backups Automáticos

```bash
# Crear script de backup
cat > /home/runner/backup_acad_micros.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/backups/acad_micros"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup de PostgreSQL
docker compose -f /ruta/a/repositorio-acad-micos/docker-compose.prod.yml exec -T web \
    pg_dump -U desarrollo -h postgresql acad_micros > $BACKUP_DIR/db_$DATE.sql

# Backup de fixtures
docker compose -f /ruta/a/repositorio-acad-micos/docker-compose.prod.yml exec -T web \
    python manage.py dumpdata > $BACKUP_DIR/fixtures_$DATE.json

# Limpiar backups antiguos (mantener últimos 30 días)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.json" -mtime +30 -delete

echo "Backup completado: $DATE"
EOF

chmod +x /home/runner/backup_acad_micros.sh

# Agregar a crontab (diario a las 2 AM)
crontab -e
# Agregar línea:
# 0 2 * * * /home/runner/backup_acad_micros.sh >> /var/log/acad_micros_backup.log 2>&1
```

## 🔄 Actualizaciones

### Actualizar Código en Producción

```bash
# 1. Entrar al directorio del proyecto
cd /ruta/a/repositorio-acad-micos

# 2. Hacer backup antes de actualizar
make db-backup-sql

# 3. Descargar últimos cambios
git pull origin main

# 4. Reconstruir imagen
make prod-build

# 5. Detener servicios
make prod-down

# 6. Levantar con nueva imagen
make prod-up

# 7. Ejecutar migraciones
make prod-migrate

# 8. Recolectar estáticos
make prod-collectstatic

# 9. Verificar que todo funcione
make prod-logs
```

## 🔧 Mantenimiento

### Ver Logs

```bash
# Logs en tiempo real
make prod-logs

# Últimas 100 líneas
docker compose -f docker-compose.prod.yml logs --tail=100

# Logs de servicio específico
docker compose -f docker-compose.prod.yml logs web
```

### Reiniciar Servicios

```bash
# Reiniciar todos los servicios
make prod-restart

# Reiniciar solo web
docker compose -f docker-compose.prod.yml restart web
```

### Ejecutar Comandos Django

```bash
# Shell de Django
docker compose -f docker-compose.prod.yml exec web python manage.py shell

# Crear usuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Ver migraciones pendientes
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

## 🔍 Troubleshooting

### Error: "No module named 'X'"

```bash
# Reconstruir imagen sin caché
docker compose -f docker-compose.prod.yml build --no-cache
```

### Error: "Database connection refused"

```bash
# Verificar que PostgreSQL esté corriendo
docker compose -f docker-compose.prod.yml ps

# Ver logs de PostgreSQL
docker compose -f docker-compose.prod.yml logs db
```

### Los archivos estáticos no se cargan

```bash
# Recolectar estáticos manualmente
make prod-collectstatic

# Verificar permisos
sudo chown -R $USER:$USER /home/instalar/static/acad_micros/
sudo chmod -R 755 /home/instalar/static/acad_micros/
```

### Contenedor web se detiene constantemente

```bash
# Ver logs completos
make prod-logs

# Verificar recursos del servidor
free -h
df -h

# Verificar variables de entorno
docker compose -f docker-compose.prod.yml config
```

## 📊 Monitoreo

### Configurar Monitoreo Básico

```bash
# Crear script de health check
cat > /home/runner/healthcheck_acad_micros.sh << 'EOF'
#!/bin/bash
ENDPOINT="http://localhost:8000/docencia/acad_micros/"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)

if [ $RESPONSE -eq 200 ]; then
    echo "OK: Aplicación respondiendo correctamente"
    exit 0
else
    echo "ERROR: Aplicación no responde (HTTP $RESPONSE)"
    # Reiniciar servicios
    cd /ruta/a/repositorio-acad-micos
    docker compose -f docker-compose.prod.yml restart web
    exit 1
fi
EOF

chmod +x /home/runner/healthcheck_acad_micros.sh

# Agregar a crontab (cada 5 minutos)
# */5 * * * * /home/runner/healthcheck_acad_micros.sh >> /var/log/acad_micros_health.log 2>&1
```

## 🆘 Soporte

Para problemas o preguntas:
- Revisar logs: `make prod-logs`
- Verificar documentación: `doc/`
- Contactar al equipo DCC

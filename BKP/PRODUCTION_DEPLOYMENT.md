# Despliegue de Producción - Repositorio Académicos

Esta guía describe cómo desplegar el servicio Django "acad_micros" en producción usando Docker Compose de manera encapsulada e independiente.

## 📋 Características del Despliegue de Producción

- **Encapsulado**: No hereda configuraciones de otros proyectos
- **Auto-contenido**: Base de datos PostgreSQL propia en el mismo compose
- **Stateless**: Sin volúmenes de media/static/logs (ephemeral para uso académico)
- **Staticfiles pre-colectados**: `collectstatic` se ejecuta durante el build de la imagen
- **Health checks**: Monitoreo automático de servicios
- **Redes duales**: Red interna para DB + red externa para Nginx

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────┐
│         Nginx Proxy (Externo)               │
│           proxy_net (externa)               │
└────────────────┬────────────────────────────┘
                 │
                 │ nginx-proxy network
                 │
        ┌────────▼─────────┐
        │   acad_micros    │  Container Django
        │   (port 8000)    │  - Gunicorn
        │                  │  - Health check: /health
        └────────┬─────────┘
                 │
                 │ internal_net
                 │
        ┌────────▼──────────────┐
        │ acad_micros_postgres  │  Container PostgreSQL 13
        │   (port 5432)         │  - Health check: pg_isready
        │                       │  - Volume: acad_micros_pgdata
        └───────────────────────┘
```

## 🔧 Configuración Inicial

### 0. Validar Configuración (Recomendado)

Antes de comenzar, ejecuta el script de validación:

```bash
make prod-validate
```

O directamente:

```bash
bash validate-prod-setup.sh
```

Este script verificará:
- ✅ Archivos requeridos existen
- ✅ Variables de entorno configuradas
- ✅ Docker y Docker Compose disponibles
- ✅ Sintaxis de archivos Python correcta
- ✅ Red de Nginx detectada (si está disponible)

### 1. Detectar la Red de Nginx

Primero, necesitas identificar el nombre de la red Docker donde está corriendo Nginx:

```bash
# Listar todas las redes Docker
docker network ls

# Inspeccionar el contenedor nginx para ver sus redes
docker inspect nginx --format '{{range $k,$v := .NetworkSettings.Networks}}{{println $k}}{{end}}'
```

O usando el Makefile:

```bash
make prod-detect-network
```

**Ejemplo de salida esperada:**
```
nginx-proxy
```

### 2. Actualizar docker-compose.prod.yml

Edita el archivo `docker-compose.prod.yml` y actualiza el nombre de la red externa en la sección `proxy_net`:

```yaml
networks:
  internal_net:
    internal: true
  proxy_net:
    external: true
    name: nginx-proxy  # ⚠️ Cambiar esto por el nombre real de tu red
```

### 3. Crear archivo .env.prod

Crea el archivo de configuración de producción desde la plantilla:

```bash
make prod-env-setup
```

O manualmente:

```bash
cp .env.prod.sample .env.prod
```

**Edita `.env.prod` y configura los valores reales:**

```bash
# Django Configuration
DJANGO_SECRET_KEY=tu-clave-secreta-aleatoria-muy-larga-y-unica
DJANGO_DEBUG=False
ALLOWED_HOSTS=apps.dcc.uchile.cl,localhost
DJANGO_SETTINGS_MODULE=memoria.settings.prod

# Database Configuration
POSTGRES_DB=acad_micros
POSTGRES_USER=acad_micros
POSTGRES_PASSWORD=tu-password-super-seguro-aqui
POSTGRES_HOST=acad_micros_postgres
POSTGRES_PORT=5432

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS=https://apps.dcc.uchile.cl

# Optional
DJANGO_LOG_LEVEL=INFO
```

**⚠️ IMPORTANTE:**
- Cambia `DJANGO_SECRET_KEY` por una clave única y aleatoria
- Cambia `POSTGRES_PASSWORD` por una contraseña segura
- **NO subas `.env.prod` al repositorio** (ya está en `.gitignore`)

### 4. Generar Django Secret Key

Para generar una clave secreta segura:

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## 🚀 Despliegue

### Inicialización Completa

Si es la primera vez que despliegas, usa el comando de inicialización:

```bash
# Inicialización guiada
make prod-init

# O paso a paso:
make prod-validate      # 0. Validar configuración
make prod-env-setup     # 1. Crear .env.prod
make prod-detect-network # 2. Detectar red de Nginx
# ... editar docker-compose.prod.yml y .env.prod ...
make prod-build         # 3. Construir imagen
make prod-up            # 4. Levantar servicios
make prod-migrate       # 5. Ejecutar migraciones
```

### Pasos Manuales

#### 1. Construir la Imagen

```bash
make prod-build
```

O directamente:

```bash
docker compose -f docker-compose.prod.yml build
```

**Nota:** Durante el build se ejecutará `collectstatic` automáticamente y los archivos estáticos quedarán embebidos en la imagen.

#### 2. Levantar Servicios

```bash
make prod-up
```

O directamente:

```bash
docker compose -f docker-compose.prod.yml up -d
```

Esto levanta:
- `acad_micros`: Contenedor Django con Gunicorn
- `acad_micros_postgres`: Contenedor PostgreSQL 13

#### 3. Verificar Estado

```bash
make prod-status
```

O:

```bash
docker compose -f docker-compose.prod.yml ps
```

Deberías ver ambos contenedores en estado `healthy`.

#### 4. Ejecutar Migraciones

```bash
make prod-migrate
```

O:

```bash
docker compose -f docker-compose.prod.yml exec acad_micros python manage.py migrate
```

#### 5. Verificar Logs

```bash
# Ver logs del servicio Django
make prod-logs

# Ver logs de PostgreSQL
make prod-logs-postgres
```

#### 6. Verificar Health Check

```bash
make prod-health
```

O directamente (desde dentro del servidor):

```bash
curl http://localhost:8000/health
# Respuesta esperada: {"status":"healthy"}
```

## 🔄 Operaciones Comunes

### Ver Logs en Tiempo Real

```bash
make prod-logs
```

### Reiniciar Servicios

```bash
make prod-restart
```

### Detener Servicios

```bash
make prod-down
```

### Abrir Shell en el Contenedor

```bash
make prod-shell
```

### Ejecutar Comandos Django

```bash
# Shell de Django
docker compose -f docker-compose.prod.yml exec acad_micros python manage.py shell

# Crear superusuario
docker compose -f docker-compose.prod.yml exec acad_micros python manage.py createsuperuser

# Otros comandos Django
docker compose -f docker-compose.prod.yml exec acad_micros python manage.py <comando>
```

## 🔍 Verificación

### Checklist Post-Despliegue

- [ ] Ambos contenedores están en estado `healthy`: `make prod-status`
- [ ] Health endpoint responde: `curl http://localhost:8000/health`
- [ ] Nginx puede alcanzar el servicio: `curl http://acad_micros:8000/health` (desde container nginx)
- [ ] Logs no muestran errores: `make prod-logs`
- [ ] La aplicación es accesible a través de Nginx en el dominio configurado

### Verificar Redes

```bash
# Ver redes del contenedor acad_micros
docker inspect acad_micros --format '{{range $k,$v := .NetworkSettings.Networks}}{{println $k}}{{end}}'

# Debería mostrar:
# internal_net
# nginx-proxy (o el nombre de tu red externa)
```

### Verificar Conectividad con Nginx

Desde dentro del contenedor de Nginx:

```bash
docker exec nginx wget --spider http://acad_micros:8000/health
```

## 🛠️ Troubleshooting

### Contenedor no arranca

```bash
# Ver logs detallados
docker compose -f docker-compose.prod.yml logs acad_micros

# Ver eventos del contenedor
docker events --filter container=acad_micros
```

### Health check falla

```bash
# Probar manualmente desde dentro del contenedor
docker compose -f docker-compose.prod.yml exec acad_micros nc -z 127.0.0.1 8000

# También puedes probar el endpoint de health directamente
docker compose -f docker-compose.prod.yml exec acad_micros sh -c "echo -e 'GET /health HTTP/1.0\r\n\r\n' | nc 127.0.0.1 8000"

# Verificar que Gunicorn está escuchando
docker compose -f docker-compose.prod.yml exec acad_micros netstat -tlnp 2>/dev/null | grep 8000 || docker compose -f docker-compose.prod.yml exec acad_micros ss -tlnp | grep 8000
```

### Error de conexión a PostgreSQL

```bash
# Verificar que Postgres está healthy
docker compose -f docker-compose.prod.yml ps acad_micros_postgres

# Ver logs de Postgres
docker compose -f docker-compose.prod.yml logs acad_micros_postgres

# Probar conexión desde el contenedor Django
docker compose -f docker-compose.prod.yml exec acad_micros nc -zv acad_micros_postgres 5432
```

### Nginx no puede alcanzar el servicio

```bash
# Verificar que acad_micros está en la red correcta
docker network inspect nginx-proxy | grep acad_micros

# Si no aparece, revisar que el nombre de la red en docker-compose.prod.yml es correcto
```

### Staticfiles no se sirven

Los staticfiles están embebidos en la imagen Docker durante el build. Si hay problemas:

```bash
# Verificar que existen en la imagen
docker compose -f docker-compose.prod.yml exec acad_micros ls -la /usr/src/app/staticfiles/

# Rebuild la imagen si es necesario
make prod-build
```

## 🔐 Seguridad

### Variables de Entorno Sensibles

- ✅ `.env.prod` está en `.gitignore` - no se subirá al repo
- ✅ Usa contraseñas fuertes para `POSTGRES_PASSWORD`
- ✅ Usa una clave única para `DJANGO_SECRET_KEY`
- ✅ Configura `ALLOWED_HOSTS` con tus dominios reales
- ✅ `DEBUG=False` en producción

### Backup de Base de Datos

```bash
# Backup (volcado SQL)
docker compose -f docker-compose.prod.yml exec acad_micros_postgres pg_dump -U acad_micros acad_micros > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar
cat backup.sql | docker compose -f docker-compose.prod.yml exec -T acad_micros_postgres psql -U acad_micros acad_micros
```

## 📊 Monitoreo

### Health Checks Automáticos

Docker Compose monitorea automáticamente:

- **acad_micros**: Verifica `/health` cada 30 segundos
- **acad_micros_postgres**: Ejecuta `pg_isready` cada 10 segundos

Verifica el estado:

```bash
docker compose -f docker-compose.prod.yml ps
```

### Logs

```bash
# Todos los servicios
docker compose -f docker-compose.prod.yml logs -f

# Solo Django
docker compose -f docker-compose.prod.yml logs -f acad_micros

# Solo PostgreSQL
docker compose -f docker-compose.prod.yml logs -f acad_micros_postgres

# Últimas N líneas
docker compose -f docker-compose.prod.yml logs --tail=100 acad_micros
```

## 🔄 Actualización

Para actualizar el servicio con nuevos cambios:

```bash
# 1. Pull los cambios del repositorio
git pull

# 2. Rebuild la imagen (incluye nuevo código y collectstatic)
make prod-build

# 3. Recrear el contenedor
docker compose -f docker-compose.prod.yml up -d --force-recreate acad_micros

# 4. Ejecutar migraciones si hay cambios en la DB
make prod-migrate

# 5. Verificar
make prod-logs
```

## 📝 Notas Importantes

### Sobre Archivos Estáticos (Static Files)

- ✅ Se colectan durante `docker build`
- ✅ Están embebidos en la imagen Docker
- ✅ No hay volumen montado (stateless)
- ✅ Nginx debe servir los estáticos desde `/usr/src/app/staticfiles/` dentro del contenedor

### Sobre Media Files

- ⚠️ No hay volumen montado para media
- ⚠️ Los archivos subidos son ephemeral (se pierden al recrear el contenedor)
- ℹ️ Esto es aceptable para este uso académico según los requerimientos
- 💡 Si necesitas persistencia, agrega un volumen para `/usr/src/app/uploads`

### Sobre Logs

- ✅ Los logs van a stdout/stderr (capturados por Docker)
- ✅ Ver con `docker compose logs`
- ⚠️ No hay volumen montado para logs en archivos
- 💡 Para logs persistentes, configura un logging driver de Docker

## 🆘 Soporte

Para problemas o dudas:

1. Revisa esta documentación
2. Consulta los logs: `make prod-logs`
3. Verifica el health check: `make prod-health`
4. Contacta al equipo DCC

## 📚 Referencias

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/settings.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Docker Image](https://hub.docker.com/_/postgres)

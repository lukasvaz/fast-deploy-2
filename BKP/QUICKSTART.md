# Quick Start Guide - Repositorio Académicos DCC

Esta guía te ayudará a comenzar rápidamente con el proyecto.

## 🎯 Para Nuevos Desarrolladores

### Opción 1: Inicio Automático (Recomendado)

```bash
# 1. Clonar repositorio
git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
cd repositorio-acad-micos

# 2. Validar configuración
bash scripts/validate-config.sh

# 3. Inicializar proyecto automáticamente
make init-project

# 4. Crear superusuario
make docker-createsuperuser

# 5. Acceder a la aplicación
# http://localhost:8000
```

### Opción 2: Paso a Paso

```bash
# 1. Clonar y entrar al directorio
git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
cd repositorio-acad-micos

# 2. Construir imagen Docker
make docker-build

# 3. Levantar servicios
make docker-up-d

# 4. Ejecutar migraciones
make docker-migrate

# 5. Cargar datos iniciales
make docker-fixtures

# 6. Crear superusuario
make docker-createsuperuser

# 7. Ver logs
make docker-logs
```

## 🏭 Para Administradores (Producción)

### Despliegue en Servidor

```bash
# 1. En el servidor, clonar repositorio
git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
cd repositorio-acad-micos

# 2. Configurar variables de entorno
nano .env.prod
# Configurar SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS, etc.

# 3. Construir y desplegar
make prod-build
make prod-up

# 4. Ejecutar migraciones
make prod-migrate

# 5. Recolectar estáticos
make prod-collectstatic

# 6. Crear superusuario
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Ver [doc/DEPLOY.md](doc/DEPLOY.md) para guía completa.

## 📚 Para Arquitectos

### Migrar Proyecto Legacy al Template DCC

```bash
# 1. Leer documentación del template
cat "basate en este proyecto/acad_micros/README.md"

# 2. Seguir guía de migración
cat "basate en este proyecto/acad_micros/MIGRACION.md"

# 3. Revisar arquitectura actual
cat doc/ARCHITECTURE.md
```

## 🛠️ Comandos Más Usados

```bash
# Ver todos los comandos disponibles
make help

# Desarrollo local
make docker-up              # Levantar proyecto
make docker-down            # Detener proyecto
make docker-logs            # Ver logs en tiempo real
make docker-shell           # Abrir shell en contenedor
make docker-migrate         # Ejecutar migraciones
make docker-restart         # Reiniciar servicios

# Base de datos
make db-backup              # Backup JSON
make db-backup-sql          # Backup SQL
make db-shell               # Acceder a PostgreSQL

# Producción
make prod-up                # Desplegar
make prod-down              # Detener
make prod-logs              # Ver logs
make prod-restart           # Reiniciar

# Utilidades
make clean                  # Limpiar cache
make check                  # Verificar problemas
make status                 # Ver estado de contenedores
```

## 📂 Estructura del Proyecto

```
repositorio-acad-micos/
├── api/                    # API REST
├── etl/                    # Procesos ETL (DBLP, AMiner, OpenAlex)
├── front/                  # Frontend web
├── grados/                 # Grados académicos
├── persona/                # Personas/Académicos
├── universidad/            # Instituciones
├── users/                  # Autenticación
├── memoria/                # Configuración Django
├── templates/              # Templates globales
├── staticfiles/            # Archivos estáticos
├── doc/                    # 📚 Documentación
├── basate en este proyecto/  # 🎨 Template DCC
├── Makefile                # Comandos automatizados
└── README.md               # Documentación principal
```

## 🔍 Recursos Útiles

| Necesitas... | Ve a... |
|--------------|---------|
| Iniciar rápidamente | Este archivo |
| Entender la arquitectura | [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md) |
| Desplegar en producción | [doc/DEPLOY.md](doc/DEPLOY.md) |
| Migrar al template DCC | [basate en este proyecto/acad_micros/MIGRACION.md](basate%20en%20este%20proyecto/acad_micros/MIGRACION.md) |
| Comandos útiles | [doc/commands.MD](doc/commands.MD) o `make help` |
| Ver todos los docs | [doc/README.md](doc/README.md) |
| Resumen de cambios | [STANDARDIZATION_SUMMARY.md](STANDARDIZATION_SUMMARY.md) |

## 🔧 Solución de Problemas Comunes

### Error: "No se puede conectar a la base de datos"

```bash
# Verificar que PostgreSQL esté corriendo
make status

# Ver logs de la base de datos
docker compose logs db

# Reiniciar servicios
make docker-restart
```

### Error: "Puerto 8000 ya en uso"

```bash
# Detener el servicio que usa el puerto
sudo lsof -ti:8000 | xargs kill -9

# O cambiar el puerto en docker-compose.yml
```

### Error: "No module named 'X'"

```bash
# Reconstruir la imagen Docker
make docker-rebuild
```

### Los cambios en el código no se reflejan

```bash
# Si usas volúmenes de Docker, reinicia el contenedor
make docker-restart

# O reconstruye la imagen
make docker-rebuild
```

## 🎓 Aprendizaje

### Conceptos Clave

1. **Apps Django**: Módulos independientes (api, etl, front, etc.)
2. **ETL**: Extracción de datos desde fuentes externas (DBLP, AMiner, etc.)
3. **Docker**: Contenedores para desarrollo y producción
4. **Makefile**: Automatización de tareas comunes
5. **Template DCC**: Estándar institucional para proyectos Django

### Flujo de Trabajo Típico

```bash
# 1. Crear rama para nueva feature
git checkout -b feature/mi-feature

# 2. Levantar proyecto
make docker-up

# 3. Hacer cambios en el código
# Editar archivos...

# 4. Probar cambios
make docker-restart
# Verificar en http://localhost:8000

# 5. Ejecutar migraciones si modificaste modelos
make docker-migrate

# 6. Commit y push
git add .
git commit -m "Descripción de cambios"
git push origin feature/mi-feature

# 7. Crear Pull Request en GitHub
```

## 📊 Siguiente Nivel

Una vez familiarizado con lo básico:

1. **Lee la arquitectura completa**: [doc/ARCHITECTURE.md](doc/ARCHITECTURE.md)
2. **Explora el código**: Empieza por `front/views.py` o `api/views.py`
3. **Entiende el ETL**: Revisa `etl/cron.py` y servicios en `persona/services/`
4. **Contribuye**: Agrega tests, mejora documentación, o implementa nuevas features

## 🆘 Ayuda

- **Documentación completa**: [doc/README.md](doc/README.md)
- **Comandos**: `make help`
- **Template DCC**: [basate en este proyecto/acad_micros/](basate%20en%20este%20proyecto/acad_micros/)
- **Issues GitHub**: Reporta problemas en el repositorio

---

**¡Bienvenido al equipo! 🚀**

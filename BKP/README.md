# Repositorio Académicos - DCC FCFM Universidad de Chile

Sistema de gestión de perfiles académicos del Departamento de Ciencias de la Computación (DCC) de la Universidad de Chile.

## 🏗️ Arquitectura del Proyecto

Este proyecto está siendo migrado a la **arquitectura estándar DCC** basada en el template institucional ubicado en [`basate en este proyecto/acad_micros/`](basate%20en%20este%20proyecto/acad_micros/).

### Estado del Proyecto

- ✅ Template DCC creado con estructura estándar
- ⚠️ Proyecto legacy en proceso de migración
- 📋 Ver [Guía de Migración](basate%20en%20este%20proyecto/acad_micros/MIGRACION.md) para detalles

## 🚀 Inicio Rápido

### Desarrollo - Con Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
cd repositorio-acad-micos

# 2. Configurar variables de entorno
cp .env.dev .env
# Editar .env si es necesario

# 3. Levantar servicios
docker-compose up --build

# 4. Acceder a la aplicación
# http://localhost:8000
```

### Producción - Con Docker Compose

Para despliegue de producción, consulta la **[Guía de Despliegue de Producción](PRODUCTION_DEPLOYMENT.md)**.

```bash
# Inicio rápido de producción
make prod-validate    # Validar configuración
make prod-init        # Inicializar configuración
make prod-build       # Construir imagen
make prod-up          # Levantar servicios
make prod-migrate     # Ejecutar migraciones
make prod-logs        # Ver logs
```

Ver **[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)** para instrucciones detalladas.

### Desarrollo - Sin Docker

```bash
# 1. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar base de datos PostgreSQL
# Asegurarse de tener PostgreSQL corriendo y crear la base de datos

# 4. Configurar variables de entorno
export DB_NAME=memoria
export DB_USER=memoriauser
export DB_PASSWORD=memoriapassword
export DB_HOST=localhost
export DB_PORT=5432

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Cargar datos iniciales (opcional)
python manage.py loaddata universidad/fixture.json
python manage.py loaddata persona/fixtures/fixture_areas.json
python manage.py loaddata users/fixture.json

# 7. Crear superusuario
python manage.py createsuperuser

# 8. Ejecutar servidor
python manage.py runserver
```

## 📁 Estructura Actual (Legacy)

```
repositorio-acad-micos/
├── api/                    # API REST
├── etl/                    # Extracción, transformación y carga de datos
├── front/                  # Frontend y vistas
├── grados/                 # Gestión de grados académicos
├── memoria/                # Configuración del proyecto Django
├── persona/                # Modelos y lógica de personas/académicos
├── revision/               # Sistema de revisiones
├── universidad/            # Modelos de universidades e instituciones
├── users/                  # Gestión de usuarios
├── templates/              # Templates HTML globales
├── staticfiles/            # Archivos estáticos
├── uploads/                # Archivos subidos por usuarios
├── docker-compose.yml      # Configuración Docker desarrollo
├── docker-compose.prod.yml # Configuración Docker producción
├── Dockerfile              # Imagen Docker
├── entrypoint.sh           # Script de inicio
├── manage.py               # CLI de Django
└── requirements.txt        # Dependencias Python
```

## 📁 Estructura Objetivo (DCC Template)

Ver [Template DCC](basate%20en%20este%20proyecto/acad_micros/README.md) para la estructura completa.

## 🔧 Comandos Útiles

### Docker

```bash
# Construir imagen
docker-compose build

# Levantar servicios
docker-compose up

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Crear superusuario
docker-compose exec web python manage.py createsuperuser

# Ver logs
docker-compose logs -f

# Acceder al shell del contenedor
docker-compose exec web sh

# Detener servicios
docker-compose down
```

### Django

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic

# Shell de Django
python manage.py shell

# Ejecutar tests
python manage.py test
```

### Base de Datos

```bash
# Exportar datos
docker-compose exec web python manage.py dumpdata > backup.json

# Importar datos
docker-compose exec web python manage.py loaddata backup.json

# Exportar base de datos PostgreSQL
docker-compose exec db pg_dump -U memoriauser memoria > backup.sql

# Importar base de datos PostgreSQL
docker exec -i repositorio-acad-micos-db-1 psql -U memoriauser -d memoria < backup.sql
```

## 📚 Documentación

- [Documentación general](doc/)
- [Guía de migración a DCC Template](basate%20en%20este%20proyecto/acad_micros/MIGRACION.md)
- [Template DCC](basate%20en%20este%20proyecto/acad_micros/README.md)
- [Comandos útiles](doc/commands.MD)
- [Deploy en testing](doc/deploy_testing.MD)

## 🛠️ Tecnologías

- **Backend**: Django 4.1+
- **Base de datos**: PostgreSQL 15
- **Frontend**: Bootstrap 5, jQuery
- **Contenedores**: Docker, Docker Compose
- **Servidor**: Gunicorn (producción)
- **Idiomas**: Español/Inglés (django-modeltranslation)

## 📦 Apps del Proyecto

- **api**: API REST para integración externa
- **etl**: Procesos de ETL para importar datos desde fuentes externas (DBLP, AMiner, OpenAlex, etc.)
- **front**: Frontend web para usuarios
- **grados**: Gestión de grados académicos y títulos
- **persona**: Modelos y lógica de personas académicas
- **revision**: Sistema de revisión y aprobación
- **universidad**: Gestión de universidades e instituciones
- **users**: Autenticación y gestión de usuarios

## 🔐 Configuración de Producción

Ver archivo `.env.dev` como referencia. Para producción:

1. Generar una `SECRET_KEY` segura
2. Configurar `DEBUG=False`
3. Definir `ALLOWED_HOSTS` apropiadamente
4. Usar `DJANGO_SETTINGS_MODULE=memoria.settings.prod`
5. Configurar variables de base de datos de producción

## 🤝 Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Universidad de Chile - DCC FCFM

## 📞 Contacto

Departamento de Ciencias de la Computación - Universidad de Chile

---

### Traducción
Más información sobre django-modeltranslation: https://django-modeltranslation.readthedocs.io/en/latest/

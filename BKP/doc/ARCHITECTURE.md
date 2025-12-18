# Arquitectura del Sistema - Repositorio Académicos

## 📐 Visión General

El proyecto **Repositorio Académicos** es una aplicación Django modular diseñada para gestionar perfiles académicos del Departamento de Ciencias de la Computación (DCC) de la Universidad de Chile.

## 🏗️ Arquitectura Actual vs. Template DCC

### Estado Actual (Legacy)

El proyecto sigue una estructura Django tradicional:

```
repositorio-acad-micos/
├── api/                    # API REST
├── etl/                    # Procesos ETL
├── front/                  # Frontend
├── grados/                 # Grados académicos
├── memoria/                # Configuración Django
│   ├── settings.py        # Settings monolítico
│   ├── urls.py
│   └── wsgi.py
├── persona/                # Modelos de personas
├── revision/               # Sistema de revisión
├── universidad/            # Instituciones
├── users/                  # Usuarios
└── manage.py
```

### Arquitectura Objetivo (DCC Template)

La arquitectura estándar DCC propone:

```
repositorio-acad-micos/
├── apps/                   # Apps organizadas
│   ├── api/
│   ├── etl/
│   └── ...
├── config/                 # Configuración centralizada
│   ├── settings/
│   │   ├── base.py        # Settings base
│   │   ├── dev.py         # Desarrollo
│   │   └── prod.py        # Producción
│   ├── urls.py
│   └── wsgi.py
├── fixtures/               # Datos iniciales
├── scripts/                # Scripts de deployment
└── Makefile               # Automatización
```

## 🔧 Componentes del Sistema

### 1. Apps Django

#### `api/` - API REST
- **Propósito**: Proveer endpoints REST para integración externa
- **Tecnologías**: Django REST Framework
- **Endpoints principales**:
  - `/api/academicos/` - Lista de académicos
  - `/api/publicaciones/` - Publicaciones
  - `/api/instituciones/` - Instituciones

#### `etl/` - Extract, Transform, Load
- **Propósito**: Importar y sincronizar datos desde fuentes externas
- **Fuentes de datos**:
  - DBLP (publicaciones)
  - AMiner (perfiles académicos)
  - OpenAlex (metadata académica)
  - ROR (instituciones)
- **Cron Jobs**:
  - `DblpUpdateCronJob` - Actualización de DBLP
  - `AminerUpdateCronJob` - Actualización de AMiner
  - `OpenAlexAuthorsUpdateCronJob` - Actualización de OpenAlex

#### `front/` - Frontend Web
- **Propósito**: Interfaz web para usuarios finales
- **Tecnologías**: 
  - Django Templates
  - Bootstrap 5
  - jQuery
- **Vistas principales**:
  - Lista de académicos
  - Perfil de académico
  - Búsqueda y filtros

#### `grados/` - Gestión de Grados
- **Propósito**: Administrar grados académicos y títulos
- **Modelos**: Grado, TipoGrado, etc.

#### `persona/` - Personas y Académicos
- **Propósito**: Modelos y lógica de personas académicas
- **Modelos principales**:
  - Persona
  - Academico
  - Publicacion
  - Area, Subarea
- **Servicios**:
  - DBLP client
  - AMiner client
  - OpenAlex client

#### `revision/` - Sistema de Revisión
- **Propósito**: Workflow de aprobación y revisión de cambios
- **Modelos**: Revision, EstadoRevision

#### `universidad/` - Instituciones
- **Propósito**: Gestión de universidades e instituciones
- **Modelos**:
  - Universidad
  - Unidad (departamentos, facultades)
  - OpenAlexInstitution
  - RORInstitution
- **Servicios**:
  - OpenAlex Institution Client
  - ROR Institution Client

#### `users/` - Autenticación y Usuarios
- **Propósito**: Gestión de usuarios y autenticación
- **Modelo**: User (custom)
- **Backend**: EmailBackend (autenticación por email)

### 2. Infraestructura

#### Base de Datos
- **Motor**: PostgreSQL 15
- **Configuración**:
  - Desarrollo: db container (Docker)
  - Producción: PostgreSQL externo o containerizado

#### Servidor Web
- **Desarrollo**: Django runserver
- **Producción**: Gunicorn + Nginx
  - Gunicorn: 4 workers, gthread worker class
  - Nginx: Proxy reverso y archivos estáticos

#### Almacenamiento
- **Archivos estáticos**: 
  - `/staticfiles/` - Estáticos de apps
  - `/staticfiles_collected/` - Estáticos recolectados
- **Media files**: `/uploads/` - Archivos subidos por usuarios

### 3. Configuración

#### Settings Modulares

**Base Settings** (`memoria/settings.py` actual, migrar a `config/settings/base.py`):
- Configuración compartida
- Apps instaladas
- Middleware
- Templates
- Internacionalización

**Development Settings** (migrar a `config/settings/dev.py`):
- DEBUG = True
- Base de datos local/Docker
- Email backend: console
- Configuración de desarrollo

**Production Settings** (`memoria/settings.prod.py` actual, migrar a `config/settings/prod.py`):
- DEBUG = False
- Seguridad reforzada
- Email backend: SMTP
- Configuración optimizada

#### Variables de Entorno

```env
# Django
DJANGO_SETTINGS_MODULE=memoria.settings
DJANGO_SECRET_KEY=...
DJANGO_DEBUG=True/False

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=memoria
DB_USER=...
DB_PASSWORD=...
DB_HOST=db
DB_PORT=5432

# Security
CSRF_TRUSTED_ORIGINS=...
ALLOWED_HOSTS=...
```

## 🔄 Flujo de Datos

### 1. Importación de Datos (ETL)

```
Fuentes Externas → ETL Services → Modelos Django → PostgreSQL
     ↓                  ↓               ↓
  DBLP            DblpClient       Publicacion
  AMiner          AminerClient     Academico
  OpenAlex        OpenAlexClient   Persona
  ROR             RORClient        Universidad
```

### 2. Visualización Web

```
Usuario → Frontend Views → Templates → API/Models → Database
                ↓
         Static/Media Files
```

### 3. API REST

```
Cliente Externo → API Endpoints → Serializers → Models → Database
```

## 🔐 Seguridad

### Autenticación
- Sistema de usuarios personalizado (email-based)
- Django Admin para administración
- Permisos por rol

### Configuración de Seguridad (Producción)
- `SECRET_KEY` desde variable de entorno
- `DEBUG = False`
- HTTPS (con certificado SSL)
- CSRF protection
- Secure cookies
- XSS protection

### Backups
- Backup diario de base de datos
- Fixtures JSON para datos críticos
- Almacenamiento seguro de credenciales

## 📊 Base de Datos

### Modelos Principales

```
Universidad ──┬─→ Unidad
              │
              └─→ OpenAlexInstitution
              
Persona ──→ Academico ──┬─→ Publicacion
          ↓             │
       Area/Subarea     └─→ Grado
          
User ──→ Revision
```

### Relaciones Clave
- Un académico puede tener múltiples publicaciones
- Un académico pertenece a una universidad/unidad
- Un académico puede tener múltiples grados
- Areas y subareas organizan conocimiento

## 🚀 Deployment

### Desarrollo
```bash
docker compose up
# → PostgreSQL + Django Dev Server en http://localhost:8000
```

### Producción
```bash
docker compose -f docker-compose.prod.yml up
# → PostgreSQL + Gunicorn detrás de Nginx
```

## 🧩 Extensibilidad

### Agregar Nueva App

1. Crear app en `apps/`:
```bash
python manage.py startapp nueva_app apps/nueva_app
```

2. Actualizar `apps/nueva_app/apps.py`:
```python
class NuevaAppConfig(AppConfig):
    name = 'apps.nueva_app'
```

3. Agregar a `INSTALLED_APPS`:
```python
LOCAL_APPS = [
    # ...
    'apps.nueva_app',
]
```

### Agregar Nueva Fuente ETL

1. Crear cliente en `etl/services/`:
```python
class NuevaFuenteClient:
    def fetch_data(self):
        # Implementación
        pass
```

2. Crear cron job en `etl/cron.py`:
```python
class NuevaFuenteCronJob(CronJobBase):
    # Implementación
    pass
```

3. Agregar a `CRON_CLASSES` en settings

## 📈 Monitoreo y Logging

### Logs
- Configuración en settings
- Niveles: DEBUG, INFO, WARNING, ERROR
- Handlers: Console (dev), File (prod)

### Métricas
- Django Admin para estadísticas básicas
- Logs de base de datos
- Health checks (en desarrollo)

## 🔮 Roadmap de Migración a DCC Template

1. ✅ Crear template DCC con estructura estándar
2. ✅ Documentar arquitectura actual
3. ✅ Agregar Makefile con comandos comunes
4. ⏳ Reorganizar settings (base/dev/prod)
5. ⏳ Mover apps a `/apps` (opcional)
6. ⏳ Actualizar imports y referencias
7. ⏳ Migrar fixtures a `/fixtures`
8. ⏳ Probar en desarrollo
9. ⏳ Desplegar en producción

## 📚 Referencias

- [Django Documentation](https://docs.djangoproject.com/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [12 Factor App](https://12factor.net/)
- [DCC Apps Template](../basate%20en%20este%20proyecto/acad_micros/)

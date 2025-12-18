# Documentación - Repositorio Académicos DCC

Bienvenido a la documentación del Sistema de Gestión de Perfiles Académicos del DCC - FCFM - Universidad de Chile.

## 📚 Índice de Documentación

### Guías Principales

- **[README.md](../README.md)** - Introducción general al proyecto
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura del sistema y componentes
- **[DEPLOY.md](DEPLOY.md)** - Guía completa de despliegue (desarrollo y producción)

### Template DCC

- **[Apps DCC Template](../basate%20en%20este%20proyecto/acad_micros/README.md)** - Estructura estándar institucional
- **[Guía de Migración](../basate%20en%20este%20proyecto/acad_micros/MIGRACION.md)** - Cómo migrar proyectos legacy al template

### Comandos y Operaciones

- **[commands.MD](commands.MD)** - Comandos útiles para operaciones diarias
- **[Makefile](../Makefile)** - Comandos automatizados (ver `make help`)

### Información Adicional

- **[deploy_testing.MD](deploy_testing.MD)** - Despliegue en ambiente de testing
- **[universidades_Chile.MD](universidades_Chile.MD)** - Listado de universidades chilenas con información de referencia

## 🚀 Inicio Rápido

### Para Desarrolladores

1. **Configurar entorno local**
   ```bash
   git clone https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos.git
   cd repositorio-acad-micos
   make init-project
   ```

2. **Leer documentación**
   - [Arquitectura](ARCHITECTURE.md) - Entender la estructura del proyecto
   - [README principal](../README.md) - Comandos básicos

### Para Administradores

1. **Desplegar en producción**
   - Ver [Guía de Despliegue](DEPLOY.md)

2. **Configurar backups**
   - Ver sección de backups en [DEPLOY.md](DEPLOY.md#-configurar-backups-automáticos)

### Para Arquitectos

1. **Migrar a DCC Template**
   - Leer [Template DCC](../basate%20en%20este%20proyecto/acad_micros/README.md)
   - Seguir [Guía de Migración](../basate%20en%20este%20proyecto/acad_micros/MIGRACION.md)

## 🏗️ Estructura del Proyecto

```
repositorio-acad-micos/
├── doc/                           # 📚 Documentación (estás aquí)
│   ├── README.md                  # Este archivo
│   ├── ARCHITECTURE.md            # Arquitectura del sistema
│   ├── DEPLOY.md                  # Guía de despliegue
│   ├── commands.MD                # Comandos útiles
│   └── ...
├── basate en este proyecto/       # 🎨 Template institucional DCC
│   └── acad_micros/
│       ├── README.md              # Documentación del template
│       ├── MIGRACION.md           # Guía de migración
│       └── ...ejemplos
├── api/                           # 🔌 API REST
├── etl/                           # 📥 Procesos ETL
├── front/                         # 🎨 Frontend web
├── grados/                        # 🎓 Grados académicos
├── persona/                       # 👤 Personas/Académicos
├── universidad/                   # 🏛️ Instituciones
├── users/                         # 👥 Usuarios
├── memoria/                       # ⚙️ Configuración Django
├── Makefile                       # 🛠️ Comandos automatizados
├── docker-compose.yml             # 🐳 Docker desarrollo
└── README.md                      # 📖 Documentación principal
```

## 🔑 Conceptos Clave

### Apps del Sistema

- **api**: API REST para integración externa
- **etl**: Importación desde DBLP, AMiner, OpenAlex, ROR
- **front**: Interfaz web para usuarios
- **grados**: Gestión de grados académicos
- **persona**: Modelos de personas y académicos
- **universidad**: Gestión de instituciones
- **users**: Autenticación y usuarios

### Tecnologías

- **Backend**: Django 4.1+
- **Base de datos**: PostgreSQL 15
- **Frontend**: Bootstrap 5, jQuery
- **Deployment**: Docker, Gunicorn, Nginx
- **ETL**: Integración con APIs externas

## 📖 Temas Frecuentes

### Cómo hacer...

| Tarea | Documentación |
|-------|---------------|
| Levantar el proyecto localmente | [README.md](../README.md#-inicio-rápido) |
| Desplegar en producción | [DEPLOY.md](DEPLOY.md) |
| Agregar una nueva app | [ARCHITECTURE.md](ARCHITECTURE.md#agregar-nueva-app) |
| Hacer backup de la BD | [DEPLOY.md](DEPLOY.md#configurar-backups-automáticos) |
| Migrar a DCC Template | [MIGRACION.md](../basate%20en%20este%20proyecto/acad_micros/MIGRACION.md) |
| Ver logs de producción | [DEPLOY.md](DEPLOY.md#ver-logs) |
| Ejecutar comandos Django | [commands.MD](commands.MD) |

### Comandos Más Usados

```bash
# Ver todos los comandos disponibles
make help

# Desarrollo
make docker-up              # Levantar desarrollo
make docker-logs            # Ver logs
make docker-shell           # Shell del contenedor

# Producción
make prod-up                # Levantar producción
make prod-logs              # Ver logs de producción
make prod-migrate           # Ejecutar migraciones

# Base de datos
make db-backup              # Backup en JSON
make db-backup-sql          # Backup en SQL
```

## 🔧 Solución de Problemas

Ver la sección de [Troubleshooting en DEPLOY.md](DEPLOY.md#-troubleshooting)

Problemas comunes:
- Error de conexión a base de datos
- Módulos no encontrados
- Archivos estáticos no se cargan
- Contenedor se detiene constantemente

## 🤝 Contribuir

Para contribuir al proyecto:

1. Fork el repositorio
2. Crear rama feature (`git checkout -b feature/mi-feature`)
3. Commit cambios (`git commit -am 'Agregar feature'`)
4. Push a la rama (`git push origin feature/mi-feature`)
5. Crear Pull Request

Ver también las [buenas prácticas del template DCC](../basate%20en%20este%20proyecto/acad_micros/README.md)

## 📞 Contacto y Soporte

- **Equipo**: DCC FCFM Universidad de Chile
- **Repositorio**: https://github.com/DCC-FCFM-UCHILE/repositorio-acad-micos
- **Documentación**: Ver este directorio `/doc`

---

**Última actualización**: Octubre 2025  
**Versión**: 1.0 (migración a DCC Template en progreso)

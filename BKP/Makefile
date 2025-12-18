# Repositorio Académicos - Makefile
# Comandos comunes para desarrollo y despliegue

.PHONY: help install migrate run test lint shell collectstatic clean docker-build docker-up docker-down

help: ## Mostrar esta ayuda
	@echo "=== Repositorio Académicos - DCC FCFM UCHILE ==="
	@echo ""
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# ========== Comandos locales (sin Docker) ==========

install: ## Instalar dependencias localmente
	pip install -r requirements.txt

migrate: ## Ejecutar migraciones localmente
	python manage.py makemigrations
	python manage.py migrate

fixtures: ## Cargar fixtures iniciales
	python manage.py loaddata ./universidad/fixtures/universidad_fixture_25_11_2025.json 2>/dev/null || echo "  ⚠️  universidad fixtures no encontrados"
	python manage.py loaddata ./users/fixtures/users_fixture_17_11_2025.json 2>/dev/null || echo "  ⚠️  users fixtures no encontrados"
	python manage.py loaddata ./persona/fixtures/persona_fixture_25_11_2025.json 2>/dev/null || echo "  ⚠️  persona fixtures no encontrados"
	python manage.py loaddata ./grados/fixtures/grados_fixture_25_11_2025.json 2>/dev/null || echo "  ⚠️  grados fixtures no encontrados"


run: ## Ejecutar servidor de desarrollo localmente
	python manage.py runserver 0.0.0.0:8000

test: ## Ejecutar tests
	python manage.py test

lint: ## Ejecutar linters
	@echo "Ejecutando pylint..."
	pylint --load-plugins pylint_django --django-settings-module=memoria.settings api etl front grados persona revision universidad users || true
	@echo "Ejecutando mypy..."
	mypy . --config-file=mypy.ini || true

shell: ## Abrir shell de Django
	python manage.py shell

createsuperuser: ## Crear superusuario
	python manage.py createsuperuser

collectstatic: ## Recolectar archivos estáticos
	python manage.py collectstatic --noinput

clean: ## Limpiar archivos temporales y cache
	@echo "Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".DS_Store" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Limpieza completada"

# ========== Comandos Docker - Desarrollo ==========

docker-build: ## Construir imagen Docker
	docker-compose build

docker-up: ## Levantar contenedores de desarrollo
	docker-compose up

docker-up-d: ## Levantar contenedores en background
	docker-compose up -d

docker-down: ## Detener y remover contenedores
	docker-compose down

docker-down-v: ## Detener y remover contenedores y volúmenes
	docker-compose down -v

docker-logs: ## Ver logs de contenedores
	docker-compose logs -f

docker-shell: ## Abrir shell en contenedor web
	docker-compose exec web sh

docker-migrate: ## Ejecutar migraciones en Docker
	docker-compose exec web python manage.py makemigrations
	docker-compose exec web python manage.py migrate

docker-fixtures: ## Cargar fixtures en Docker
							
	## universidad
	docker-compose exec web python manage.py loaddata universidad/fixtures/universidad_fixture_15_10_25.json || true

	## users
	docker-compose exec web python manage.py loaddata users/fixtures/users_fixture_3_10_2025.json
	docker-compose exec web python manage.py loaddata users/fixtures/users_fixture_15_10_25.json

	## grados
	docker-compose exec web python manage.py loaddata grados/fixtures/grados_fixture_15_10_25.json

	## fixture_areas
	docker-compose exec web python manage.py loaddata persona/fixtures/fixture_areas.json || true
	docker-compose exec web python manage.py loaddata persona/fixtures/persona_fixture_15_10_25.json || true

docker-createsuperuser: ## Crear superusuario en Docker
	docker-compose exec web python manage.py createsuperuser

docker-collectstatic: ## Recolectar estáticos en Docker
	docker-compose exec web python manage.py collectstatic --noinput

docker-shell-django: ## Abrir shell de Django en Docker
	docker-compose exec web python manage.py shell

docker-restart: ## Reiniciar contenedores
	docker-compose restart

docker-rebuild: ## Reconstruir y levantar contenedores
	docker-compose down
	docker-compose build --no-cache
	docker-compose up

# ========== Comandos Docker - Producción ==========

prod-build: ## Construir imagen de producción
	docker compose -f docker-compose.prod.yml build

prod-up: ## Levantar en producción
	docker compose -f docker-compose.prod.yml up -d --remove-orphans

prod-down: ## Detener producción
	docker compose -f docker-compose.prod.yml down

prod-down-v: ## Detener producción y eliminar volúmenes (⚠️ borra datos)
	docker compose -f docker-compose.prod.yml down -v --remove-orphans
	@echo "✅ Servicios detenidos y volúmenes eliminados"

prod-logs: ## Ver logs de producción
	docker compose -f docker-compose.prod.yml logs -f acad_micros

prod-logs-postgres: ## Ver logs de PostgreSQL
	docker compose -f docker-compose.prod.yml logs -f acad_micros_postgres

prod-makemigrations: ## Generar migraciones en producción (si hay cambios de modelos)
	docker compose -f docker-compose.prod.yml exec acad_micros python manage.py makemigrations

prod-migrate: ## Ejecutar migraciones en producción
	docker compose -f docker-compose.prod.yml exec acad_micros python manage.py migrate

prod-shell: ## Abrir shell en contenedor de producción
	docker compose -f docker-compose.prod.yml exec acad_micros sh

prod-restart: ## Reiniciar servicios de producción
	docker compose -f docker-compose.prod.yml restart

prod-status: ## Ver estado de servicios de producción
	docker compose -f docker-compose.prod.yml ps

prod-health: ## Verificar health check del servicio
	@echo "🏥 Verificando health del servicio acad_micros..."
	@docker compose -f docker-compose.prod.yml exec acad_micros sh -c "nc -z 127.0.0.1 8000 && echo '✅ Puerto 8000 responde' || echo '❌ Puerto 8000 no responde'"
	@docker compose -f docker-compose.prod.yml exec acad_micros sh -c "echo -e 'GET /health HTTP/1.0\r\n\r\n' | nc 127.0.0.1 8000 | grep -o '{.*}' || echo '⚠️  Health endpoint no responde correctamente'"

# Comandos de configuración de producción

prod-validate: ## Validar configuración antes de desplegar
	@bash validate-prod-setup.sh

prod-detect-network: ## Detectar network de Nginx
	@echo "🔍 Detectando redes de Docker..."
	@docker network ls
	@echo ""
	@echo "📋 Para detectar la red de Nginx ejecute:"
	@echo "   docker inspect nginx --format '{{range \$$k,\$$v := .NetworkSettings.Networks}}{{println \$$k}}{{end}}'"
	@echo ""
	@echo "⚙️  Actualice docker-compose.prod.yml con el nombre correcto de la red"

prod-env-setup: ## Crear archivo .env.prod desde plantilla
	@if [ ! -f .env.prod ]; then \
		cp .env.prod.sample .env.prod; \
		echo "✅ Archivo .env.prod creado desde .env.prod.sample"; \
		echo "⚠️  IMPORTANTE: Edite .env.prod y cambie los valores CHANGE_ME"; \
	else \
		echo "⚠️  El archivo .env.prod ya existe. No se sobrescribirá."; \
	fi

prod-init: prod-env-setup ## Inicializar configuración de producción (paso a paso)
	@echo "🚀 Inicialización de producción - MANUAL"
	@echo ""
	@echo "Pasos a ejecutar:"
	@echo "  1. Editar .env.prod con valores reales (DJANGO_SECRET_KEY, POSTGRES_PASSWORD)"
	@echo "  2. Verificar network de Nginx: make prod-detect-network"
	@echo "  3. Actualizar docker-compose.prod.yml con el nombre correcto de proxy_net"
	@echo "  4. Construir imagen: make prod-build"
	@echo "  5. Levantar servicios: make prod-up"
	@echo "  6. Verificar logs: make prod-logs"
	@echo "  7. Ejecutar migraciones: make prod-migrate"

prod-full-init: prod-env-setup ## 🚀 Inicialización COMPLETA de producción (automática)
	@echo "🚀 Inicialización COMPLETA de producción..."
	@echo ""
	@echo "⏸️  Pauses para configuración:"
	@echo "  1. Revisar .env.prod - asegúrate de editar DJANGO_SECRET_KEY y POSTGRES_PASSWORD"
	@echo ""
	@read -p "¿Has editado .env.prod con valores reales? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Abortado. Por favor edita .env.prod primero."; \
		exit 1; \
	fi
	@echo ""
	@echo "⚠️  ADVERTENCIA: Esta operación limpiará la BD de producción."
	@read -p "¿Está seguro? [y/N] " -n 1 -r; \
	echo; \
	if [[ ! $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "❌ Abortado."; \
		exit 1; \
	fi
	@echo ""
	@echo "🧹 Limpiando BD anterior..."
	@make prod-down-v
	@echo ""
	@echo "📋 Paso 1: Validar configuración..."
	@make prod-validate
	@echo ""
	@echo "🔨 Paso 2: Construir imagen de producción (esto puede tardar)..."
	@make prod-build
	@echo ""
	@echo "⬆️  Paso 3: Levantar servicios..."
	@make prod-up
	@echo ""
	@echo "⏳ Esperando a que PostgreSQL esté listo..."
	@sleep 15
	@echo ""
	@echo "🔄 Paso 4: Generar y ejecutar migraciones..."
	@docker compose -f docker-compose.prod.yml exec acad_micros python manage.py makemigrations
	@make prod-migrate
	@echo ""
	@echo "📦 Paso 5: Cargar fixtures iniciales..."
	@docker compose -f docker-compose.prod.yml exec acad_micros python manage.py loaddata universidad/fixtures/fixture.json || true
	@docker compose -f docker-compose.prod.yml exec acad_micros python manage.py loaddata persona/fixtures/fixture_areas.json || true
	@docker compose -f docker-compose.prod.yml exec acad_micros python manage.py loaddata users/fixtures/fixture.json || true
	@echo ""
	@echo "✅ Paso 6: Verificar estado..."
	@make prod-status
	@echo ""
	@echo "✨ ¡LISTO! Tu aplicación está en producción."
	@echo ""
	@echo "Próximos pasos opcionales:"
	@echo "  • Ver logs:           make prod-logs"
	@echo "  • Health check:       make prod-health"
	@echo "  • Shell en contenedor: make prod-shell"
	@echo "  • Crear superusuario: docker compose -f docker-compose.prod.yml exec acad_micros python manage.py createsuperuser"

prod-fixtures: ## Cargar fixtures en producción
	@echo "📦 Cargando fixtures en producción..."
	docker compose -f docker-compose.prod.yml exec acad_micros python manage.py loaddata universidad/fixtures/fixture.json || true
	docker compose -f docker-compose.prod.yml exec acad_micros python manage.py loaddata persona/fixtures/fixture_areas.json || true
	docker compose -f docker-compose.prod.yml exec acad_micros python manage.py loaddata users/fixtures/fixture.json || true
	@echo "✅ Fixtures cargadas"

# ========== Base de Datos ==========

db-backup: ## Backup de base de datos (JSON)
	docker-compose exec web python manage.py dumpdata > backup_$(shell date +%Y%m%d_%H%M%S).json
	@echo "✓ Backup creado: backup_$(shell date +%Y%m%d_%H%M%S).json"

db-backup-sql: ## Backup de PostgreSQL (SQL)
	docker-compose exec db pg_dump -U memoriauser memoria > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✓ Backup SQL creado: backup_$(shell date +%Y%m%d_%H%M%S).sql"

db-restore: ## Restaurar desde fixture JSON (usar: make db-restore FILE=backup.json)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Especifique FILE=nombre_archivo.json"; \
		exit 1; \
	fi
	docker-compose exec web python manage.py loaddata $(FILE)

db-shell: ## Acceder a shell de PostgreSQL
	docker-compose exec db psql -U memoriauser -d memoria

db-reset: ## PELIGRO: Resetear base de datos
	@echo "⚠️  ADVERTENCIA: Esto eliminará todos los datos!"
	@read -p "¿Está seguro? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec web python manage.py flush --no-input; \
		echo "✓ Base de datos reseteada"; \
	fi

# ========== Utilidades ==========

check: ## Verificar problemas en el proyecto
	python manage.py check

show-migrations: ## Mostrar estado de migraciones
	python manage.py showmigrations

show-urls: ## Mostrar todas las URLs del proyecto
	python manage.py show_urls || echo "Instalar django-extensions para este comando"

init-project: ## Inicializar proyecto desde cero
	@echo "🚀 Inicializando proyecto..."
	make docker-build
	make docker-up-d
	@echo "⏳ Esperando a que los servicios estén listos..."
	sleep 10
	make docker-migrate
	make docker-fixtures
	@echo "✓ Proyecto inicializado"
	@echo ""
	@echo "Próximos pasos:"
	@echo "  1. Crear superusuario: make docker-createsuperuser"
	@echo "  2. Acceder a http://localhost:8000"

status: ## Ver estado de contenedores
	docker-compose ps

# ========== Desarrollo ==========

format: ## Formatear código con black
	black . || echo "Instalar black para formatear: pip install black"

check-format: ## Verificar formato del código
	black --check . || echo "Instalar black: pip install black"

coverage: ## Ejecutar tests con cobertura
	coverage run --source='.' manage.py test
	coverage report
	coverage html
	@echo "✓ Reporte HTML en htmlcov/index.html"

# ========== Información ==========

version: ## Mostrar versiones de dependencias
	@echo "Python: $(shell python --version)"
	@echo "Django: $(shell python -c 'import django; print(django.get_version())')"
	@echo "Docker: $(shell docker --version)"
	@echo "Docker Compose: $(shell docker-compose --version)"

env-example: ## Crear .env desde .env.dev
	cp .env.dev .env
	@echo "✓ Archivo .env creado. Edítelo según sea necesario."

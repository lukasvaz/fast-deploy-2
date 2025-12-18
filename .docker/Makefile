# makefile

build:
	docker compose --file dc-produccion.yml --project-name acad_micros up -d --build --force-recreate --remove-orphans
	docker ps

_build:
	docker compose down
	docker compose --project-name acad_micros up -d --build --force-recreate --remove-orphans
	docker ps

_init:
	docker compose down
	rm -rf ./data || true
	make _build
	docker exec acad_micros python manage.py makemigrations
	docker exec acad_micros make migrate
	docker exec acad_micros make loaddata
	docker exec acad_micros make precommit

update:
	git submodule update
	git stash
	git pull
	git stash pop

logs:
	docker logs -f acad_micros

ssh:
	docker exec -it acad_micros bash

__clean:
	docker stop acad_micros
	docker rm acad_micros
	docker stop postgresql
	docker rm postgresql
	rm -rf ./data
	make _build
	docker exec acad_micros python manage.py migrate
	docker exec acad_micros make loaddata

# Copia archivos media locales al servidor de producción
# Uso: make copy_media LOCAL_MEDIA_PATH=app/_media/acad_micros HOST=instalar@host
copy_media:
	@if [ -z "$(LOCAL_MEDIA_PATH)" ] || [ -z "$(HOST)" ]; then \
		echo "Debes definir LOCAL_MEDIA_PATH y HOST. Ejemplo: make copy_media LOCAL_MEDIA_PATH=app/_media/acad_micros HOST=instalar@host"; \
		exit 1; \
	fi
	scp -r $(LOCAL_MEDIA_PATH)/* $(HOST):/home/instalar/media/acad_micros/
	ssh $(HOST) 'chown -R instalar:instalar /home/instalar/media/acad_micros/'

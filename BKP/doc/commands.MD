## Dumpdata
- docker compose --env-file .env.docker.dev exec   web python manage.py dumpdata universidad persona users> ./fixture_test.json // django fixture
- pg_dump -h localhost -p {LOCAL_PORT} -U {DB_USER} -d {DB_NAME} > memoria_backup.sql // raw sql
## Loaddata
docker compose --env-file .env.docker.dev exec web python manage.py loaddata FILE // django fixture
docker exec  -i memoria-repositorio-academicos-db-1 psql -U memoriauser -d memoria < database_backup.sql  // raw sql
# Access to containers
sudo docker exec -it  memoria-repositorio-academicos-db-1 sh
sudo docker exec -it  memoria-repositorio-academicos-web-1 sh

# clean db 
docker compose --env-file .env.docker.dev  exec web python manage.py  flush --no-input

# Run commands locally
python -m dotenv -f .env.local.dev run -- python COMMMAND

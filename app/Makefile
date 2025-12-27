loaddata:
	python manage.py loaddata _fixtures/users/fixtures/users_fixture_23_12_2025.json
	python manage.py loaddata _fixtures/universidad/fixtures/universidad_fixture_23_12_2025.json
	python manage.py loaddata _fixtures/persona/fixtures/persona_fixture_23_12_2025.json
	python manage.py loaddata _fixtures/grados/fixtures/grados_fixture_23_12_2025.json

# backup:
# 	mkdir bkp
# 	python manage.py dumpdata backend --indent 2 > bkp/backend.json
# 	zip _backup/backup.zip bkp/*.json
# 	rm -rf bkp

dumpdata:
	python manage.py dumpdata universidad --indent 2 > _fixtures/universidad/fixtures/universidad_fixture_23_12_2025.json
	python manage.py dumpdata users --indent 2 > _fixtures/users/fixtures/users_fixture_23_12_2025.json
	python manage.py dumpdata persona --indent 2 > _fixtures/persona/fixtures/persona_fixture_23_12_2025.json
	python manage.py dumpdata grados --indent 2 > _fixtures/grados/fixtures/grados_fixture_23_12_2025.json

precommit:
	isort . --skip ./sso --skip ./users --settings-path pyproject.toml
	black . --config pyproject.toml
	flake8 . --config .flake8
	djlint . --reformat

bandit:
	bandit -r .

rate:
	pylint *

deadcode:
	vulture . --min-confidence 100

healthcheck:
	make rate
	make deadcode

migrations:
	python manage.py makemigrations
	make precommit

migrate:
	python manage.py migrate

update:
	pur -r _requirements/base.txt
	pur -r _requirements/production.txt

docs:
	mkdir -p /docs/images
	python manage.py graph_models --pygraphviz  auth --exclude-models BaseModel,AbstractBaseUser,PermissionsMixin,AbstractUser,Permission,Group -g -o /docs/images/auth.png
	python manage.py graph_models --pygraphviz polls -g -o /docs/images/polls.png
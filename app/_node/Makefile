# makefile

update:
	npm install -g npm-check-updates
	ncu --upgrade

	@printf '\n\n$(bold)Instalando Node Modules$(sgr0)\n'
	npm install
	
	rm -rf ../_staticfiles/vendor
	rm -rf ../_staticfiles/images/bootstrap-icons

	@printf '\n$(bold)Actualizando Bootstrap$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/bootstrap
	cp -r node_modules/bootstrap/dist/* ../_staticfiles/vendor/bootstrap
	npm run sass-prod

	@printf '\n$(bold)Actualizando Bootstrap Icons$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/bootstrap-icons
	cp -r node_modules/bootstrap-icons/font/* ../_staticfiles/vendor/bootstrap-icons

	mkdir -p ../_staticfiles/images/bootstrap-icons
	cp -r node_modules/bootstrap-icons/icons/* ../_staticfiles/images/bootstrap-icons

	@printf '\n$(bold)Actualizando Bootstrap Plugin: Table$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/bootstrap-table
	cp -r node_modules/bootstrap-table/dist/* ../_staticfiles/vendor/bootstrap-table

	@printf '\n$(bold)Actualizando HTMX$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/htmx
	cp -r node_modules/htmx.org/dist/* ../_staticfiles/vendor/htmx

	@printf '\n$(bold)Actualizando ChartJS Plugin: ColorSchemes$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/chart.js
	cp -r node_modules/chart.js/dist/* ../_staticfiles/vendor/chart.js

	@printf '\n$(bold)Actualizando jQuery$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/jquery
	cp -r node_modules/jquery/dist/* ../_staticfiles/vendor/jquery

	@printf '\n$(bold)Actualizando Intl Tel Input$(sgr0)\n'
	mkdir -p ../_staticfiles/vendor/intl-tel-input
	cp -r node_modules/intl-tel-input/build/* ../_staticfiles/vendor/intl-tel-input

dev:
	npm run sass-dev
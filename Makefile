run:
	python manage.py runserver

test:
	python -Wa manage.py test

runprod:
	gunicorn dhs.asgi:application -k uvicorn.workers.UvicornWorker

migrate:
	python manage.py migrate

shell:
	python manage.py shell

typecheck:
	mypy cegs_portal scripts utils config

loaddata:
	scripts/load_gencode_gff3_data.sh ../cegs_portal_data/other/gencode.v38.annotation.gff3 GRCh38 13
	scripts/load_gencode_gff3_data.sh ../cegs_portal_data/other/gencode.v19.annotation.gff3 GRCh37
	scripts/load_klann_2021_wgceres_data.sh ../cegs_portal_data/wgCERES/experiment.json
	scripts/load_klann_2021_scceres_data.sh ../cegs_portal_data/scCERES/K562/experiment.json
	scripts/load_screen_ccres.sh ../cegs_portal_data/screen/file.json GRCh37

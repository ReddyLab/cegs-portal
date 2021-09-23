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

loaddata:
	scripts/load_gencode_gff3_data.sh ../cegs_portal_data/other/gencode.v38.annotation.gff3 GRCh38 13
	scripts/load_gencode_gff3_data.sh ../cegs_portal_data/other/gencode.v19.annotation.gff3 GRCh37
	scripts/load_wgceres_data.sh ../cegs_portal_data/wgCERES/experiment.json

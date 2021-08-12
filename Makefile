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
	# python manage.py shell -c 'import load_gff3_data; load_gff3_data.run()'
	python manage.py shell -c 'import load_wgceres_data; load_wgceres_data.run()'

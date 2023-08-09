run:
	python manage.py runserver

test:
	python -Wa manage.py test

runprod:
	gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker

migrate:
	python manage.py migrate

shell:
	python manage.py shell

typecheck:
	mypy cegs_portal scripts utils config

exp_cov:
	./scripts/data_generation/gen_experiment_coverage_viz.sh

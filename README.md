# CEGS CCGR Portal

Duke CCGR Functional Genomics Portal

<a href="https://github.com/pydanny/cookiecutter-django/"><img src="https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter" alt="Built with Cookiecutter Django"/></a>
<a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Black code style"/></a>

License: [MIT](LICENSE)

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Set up Devlopment Environment

First, clone this repository. This is a Django 4.x project that requires Python >= 3.9. Additionally you'll need at least Node.js 14.17 for CSS auto-reloading and compilation. The database, PostgreSQL, can [downloaded here](https://www.postgresql.org/download/) but the easiest way to set up the database is using Docker compose or, if you're on a Mac, [Postgres.app](https://postgresapp.com).

These instructions are for unix/linux systems. Windows users can follow along if they want to use WSL to run the portal.

### Pre-reqs

-   [python](https://www.python.org) >= 3.9
-   [docker](http://docker.com)
-   [Node.js](https://nodejs.dev) >= 14.17
-   [Rust](https://www.rust-lang.org)

Once you have the repository cloned and the pre-reqs installed you need to install the dependencies.

    $ cd [portal directory]
    $ # set up "virtual environment" using method of your choice (optional)
    $ pip install -r requirements/local.txt
    $ npm install

Then you can start the database:

    $ docker compose up -d

Before django can run, a dependency has to be manually added:

    $ cd extensions/exp_viz
    $ maturin develop
    $ cd ../..

You have to create the static data directory:

    $ mkdir cegs_portal/static_data

And create the `cegs_portal` database in your postgres container. This is left as an exercise to the reader.

You'll need to set a few environment variables:

    $ export DATABASE_URL=postgres://postgres:test_password@127.0.0.1:5432/cegs_portal
    $ export USE_DOCKER=no

Now you must run the database migrations:

    $ make migrate

And start the server:

    $ npm run dev

This will launch django and the tailwind CSS compiler. When you edit a file the django server will restart. If you edit the project.css.tw file it will get recompiled.

## Loading data

Currently there are scripts to load up the gencode gff3 files, downloadable from http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.annotation.gff3.gz and http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gff3.gz. There's an additional script for loading some wgCERES data (the data is not currently publicly available but will probably become so in the future).
NOTE: This section is in progress until we have a location the data can be downloaded from.

There are a couple of sets of publicly available data that go into the database

-   Gencode annotations for hg19 and hg38
-   Screen cCREs

The gencode gff3 data is downloadable from http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_19/gencode.v19.annotation.gff3.gz and http://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_43/gencode.v43.annotation.gff3.gz and can be added to the database using the [load_gencode_gff3_data.sh](scripts/data_loading/load_gencode_gff3_data.sh) script. See [load_all.sh](scripts/data_loading/load_all.sh) for usage.

The Screen cCREs can be downloaded from https://api.wenglab.org/screen_v13/fdownloads/V3/GRCh38-cCREs.bed The hg19 cCREs are lifted over from this file using the [UCSC liftOver tool](https://genome.ucsc.edu/goldenPath/help/hgTracksHelp.html#Liftover) and the [hg38ToHg19.over.chain](https://github.com/imbforge/liftover/raw/master/hg38ToHg19.over.chain) data file.

### A note about loading experiment data when using docker compose for the database

By default docker containers can only be 10Gb big. When loading up several experiments of data, this limit may be hit.
To get around it, [modify](https://docs.docker.com/compose/compose-file/#volumes-top-level-element) [docker-compose.yml](docker-compose.yml) to store [PG_DATA on a separate volume](https://github.com/docker-library/docs/blob/master/postgres/README.md#where-to-store-data) (See https://docs.docker.com/compose/compose-file/#volumes-top-level-element for information on docker-compose.yml changes).

## Generating Ancillary Data

Some of the visualizations use data files built from the database, but that exist outside of the database.

Download or `git clone` the [cov_viz repository](https://github.com/ReddyLab/cov_viz) and install the cov_viz utility with the command `cargo install --path [insert path to cov_viz directory here]`
Download or `git clone` the [cov_viz_manifest repository](https://github.com/ReddyLab/cov_viz_manifest) and install the cov_viz_manifest utility with the command `cargo install --path [insert path to cov_viz_manifest directory here]`
Run `make exp_cov` from the root portal directory.

## Basic Commands

### Setting Up Your Users

-   To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

-   To create an **superuser account**, use this command::

    $ python manage.py createsuperuser

For convenience, you can keep your normal user logged in on Chrome and your superuser logged in on Firefox (or similar), so that you can see how the site behaves for both kinds of users.

### Type checks

Running type checks with mypy:

    $ mypy cegs_portal

### Test coverage

To run the tests, check your test coverage, and generate an HTML coverage report::

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html

#### Running tests with py.test

    $ pytest

### Live reloading and Tailwind CSS compilation

Run "npm run dev"

## Deployment

Deployment kicks-off automatically when a push to the main branch in the cegs-portal repository is made.

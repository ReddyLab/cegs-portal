# CEGS Portal

Duke CEGS Functional Genomics Portal

<a href="https://github.com/pydanny/cookiecutter-django/"><img src="https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter" alt="Built with Cookiecutter Django"/></a>
<a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Black code style"/></a>

License: [MIT](LICENSE)

## Settings

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Set up Devlopment Environment

This is a Django 3.2 project that requires at least Python 3.8. Additionally you'll need at least Node.js 14.17 for auto-reloading and CSS compilation. The easiest
way to set up a database is using docker compose, so that's another thing to install, sorry.

Once you have all those installed you need to install dependencies.

    $ pip install -r requirements/local.txt
    $ npm install

Then you can start the database:

    $ docker compose up -d

And start the server:

    $ npm run dev

This will launch django and begin the tailwind CSS compiler. When you edit a file either server will restart. If you edit the project.css.tw file it will
get recompiled (and the server will restart).

## Basic Commands

### Setting Up Your Users

* To create a **normal user account**, just go to Sign Up and fill out the form. Once you submit it, you'll see a "Verify Your E-mail Address" page. Go to your console to see a simulated email verification message. Copy the link into your browser. Now the user's email should be verified and ready to go.

* To create an **superuser account**, use this command::

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

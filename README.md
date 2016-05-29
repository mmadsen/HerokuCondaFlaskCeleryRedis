# HerokuCondaFlaskAlembic:  Application Template #

This template is suitable for setting up a Heroku application that
runs Python applications using Anaconda Python, with the lightweight
Flask web framework, and the Alembic/Flask-Migrate database migration
manager.  

Applications built from this template assume Heroku-Postgres as the 
database backend (see below).  

The application as represented here assumes that we set up both `staging` and `production`
versions of the application on Heroku, and the instructions below reflect this.  For 
purposes of illustration, the base application name used here will be `mmadsen-test`, but 
you should choose a unique application name.


## Getting Started ##

### App Creation ###

Fork this repository (or clone it and establish a new Git versioning
database using `rm -rf .git; git init`).  Rename the directory 
to something suitable for your application.  

1.  Copy the env-template to .env 
1.  Copy slugignore-template to .slugignore
1.  Put the environment variables for configuration into your current session: `source .env` (or whatever is appropriate for your shell)
1.  Log into Heroku using `heroku login`
1.  Create staging and production applications on Heroku: 
	1.  `heroku create --buildpack https://github.com/mmadsen/conda-buildpack mmadsen-test-staging`  
	1.  `heroku create --buildpack https://github.com/mmadsen/conda-buildpack mmadsen-test-prod`
1.  Add Git "remotes" so that you can push this repository to each of the Heroku applications:
	1.  `git remote add staging git@heroku.com:mmadsen-test-staging.git`
	1.  `git remote add staging git@heroku.com:mmadsen-test-prod.git`
	1.  You may wish to clean up the remotes which ship with the template by simply editing `.git/config` and removing remote blocks which no longer apply (DO THIS CAREFULLY!)
	1.  Ensure that you still have an `origin` remote (e.g., your Github fork) for storing the canonical source code for your application.
1.  Test that you can push the repository to each Heroku application:
	1.  `git push staging master`
	1.  `git push prod master`

If this succeeds, even if we don't have everything wired up yet, then you have one source code repository which is wired via Git to two Heroku applications, one for staging and one for production use.  

### Database Creation ###

The first thing to do is make sure that your local developer box has Postgres installed, along with any client tools.  You can find instructions, downloads, etc at the [Postgresql website](https://www.postgresql.org/).  On OSX, I strongly recommend Homebrew package management for this.  

For the template, the database name I'm using is "wordcount_dev" simply because I was working with a common statistics example.  You should take this opportunity to rename the database to suit your application needs now, before you run any further commands.

1.  To create the local database:  `psql -c 'create database wordcount_dev;'`
1.  If you change the database name, change the configuration variable `DATABASE_URL` in .env and execute `source .env`
1.  Create Heroku-Postgres database add-ons for both production and staging applications.  At this point, you may want to choose different sizes; for illustration purposes here I use the free hobby-dev tier.  
	1.  `heroku addons:create heroku-postgresql:hobby-dev --app mmadsen-test-staging`
	1.  `heroku addons:create heroku-postgresql:hobby-dev --app mmadsen-test-prod`
1.  Set configuration variables on the staging and production applications, to allow them to pick up the correct information from `config.py` for their environment type:
	1.  `heroku config:set APP_SETTINGS=config.StagingConfig --remote staging`
	1.  `heroku config:set APP_SETTINGS=config.ProductionConfig --remote prod`
1.  Verify that you have correct configurations and new database URLs for each:
	1.  `heroku config --remote prod`
	1.  `heroku config --remote staging`

### Database Operations and Migrations ###

Rather than managing database schemas manually, this template app employs Alembic, a python library which manages DDL 
migrations for SQLAlchemy.  When using Flask as the web framework, we then layer Flask-Migrate on top of Alembic, to 
create a simple system for migrations which operates almost exactly like the Rails ActiveRecord system.

To set this up, first note that the module `models.py` contains our actual schema classes.  Additional modules can be imported
by simply including them in the main `web.py` application module.  Each table is represented by a class, in SQLAlchemy syntax.
When these classes are modified (or new ones added), Alembic notes the change and automatically constructs a "migration" to change the database structure to match.  Flask-Migrate and Alembic keep these version-controlled in a directory called `migrations`.  

To set up the `migrations` folder, you simply call `python manage.py db init`.  You do not need to do this given the existing 
migrations in the template app, but it is necessary if you write an app structure from scratch or add Flask-Migrate to an existing application.

Once the DDL model classes have been modified, you apply them to the local database as follows:

1.  `python manage.py db migrate` -- this creates the next migration file.  You may want to edit this manually before proceeding.
1.  `python manage.py db upgrade` -- this **applies** the latest migration.  

To apply the migrations to Heroku applications, in production and staging:

1.  Check in the changes to version control.
1.  Push the changes to both staging and production:  `git push staging master` or `git push prod master`
1.  Use `heroku run` to execute the migration on the remote applications, just as you did on the local database.
1.  NOTE:  Make sure you have the configuration variables for `APP_SETTINGS` set on the remote applications, so it can pick up the proper database URL.
	1.  `heroku run python manage.py db upgrade --app mmadsen-test-staging`
	1.  `heroku run python manage.py db upgrade --app mmadsen-test-prod`

Further operations are possible with `Flask-Migrate` as well.  To downgrade schemas, use `python manage.py db downgrade` for example.  You can also get migration history with `python manage.py db history`.  





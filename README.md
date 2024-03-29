# coherence-chat
Chatservice for Coherence

## Deployment pattern
During development, test with a dev flask server: `NOALERTS=1 python bot.py`.

Unit tests:

`NOALERTS=1 pytest -vv`

Before pushing to prod, test with gunicorn locally: `NOALERTS=1 gunicorn -b 0.0.0.0:5000 bot:app --workers 1`

Build the frontend into prod mode with `yarn build` inside the `web/` directory.

Then you can safely push to prod.

## alembic usage
`python manage.py db migrate`

`python manage.py db upgrade`

When you make a db migration, go to the alembic file and remove all the apscheduler references. There's some weirdness because those tables are not created by sqlalchemy.

## ngrok for local dev
`ngrok http 5000`

Update twilio URL

## git
reset N commits locally: `git reset --hard HEAD~N`

push a non master branch to heroku master: `git push heroku +HEAD:master`

## data analysis
dump prod DB to local: delete local analysis_db, then `heroku pg:pull postgresql-slippery-57674 analysis_db --app coherence-chat`

## stripe local testing setup
open new terminal tab and do `stripe listen --forward-to 5000` to forward stripe test events to local

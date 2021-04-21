# coherence-chat
Chatservice for Coherence

## Deployment pattern
During development, test with a dev flask server: `python bot.py`.

Run pytest with `UNITTESTING=1 pytest` and ensure all is passing.

Before pushing to prod, test with gunicorn locally: `gunicorn -b 0.0.0.0:5000 bot:app --workers 1`

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

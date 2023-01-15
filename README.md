# Create Environment
> conda env create -f environment.yml
> conda activate 3hustlers
> mkdir gpt3_logs

# Environment variables
Create a `.env` file similar to the `.env.sample` file and put secret keys there.

NEVER COMMIT THE ENV FILE

# Flask app
> flask run

- Flask create database
> export FLASK_APP=~/Documents/workspace/3hustlers/youtubesummarizer/src
> flask shell
> from src.database import db
> db.create_all()
> db.drop_all()

# Deploy on Heroku
> pip install gunicorn

- Create a Procfile
- Create a runner.py
> gunicorn src.runner:application

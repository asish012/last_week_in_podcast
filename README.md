# Environment variables
Create a `.env` file similar to the `.env.sample` file and put secret keys there.

**NEVER COMMIT THE ENV FILE**

# Run YouTubeSummarizer as a docker container
```sh
docker-compose up --build -d
```

## Cleanup docker environment
```sh
docker stop ytsummarizer
docker rm ytsummarizer
docker image rm youtubesummarizer
```

# Build local development environment
```sh
conda env create -f environment.yml
conda activate 3hustlers
mkdir src/logs
```

## Running Flask app
> flask run

## Flask create database (if needed)
```sh
export FLASK_APP=~/Documents/workspace/3hustlers/youtubesummarizer/src
flask shell
from src.database import db
db.create_all()
db.drop_all()
```

# Deploy on Heroku
- Create a Procfile
- Create a runner.py

```sh
pip install gunicorn
gunicorn src.runner:application
```

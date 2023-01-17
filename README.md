# Create Environment
```sh
conda env create -f environment.yml
conda activate 3hustlers
cd src
mkdir logs
cd ..
```

# Environment variables
Create a `.env` file similar to the `.env.sample` file and put secret keys there.

**NEVER COMMIT THE ENV FILE**


# Running Flask app
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

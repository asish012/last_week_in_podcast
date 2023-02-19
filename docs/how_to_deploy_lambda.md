
sam init
sam build
sam local invoke ArticleScraperFunction -e events/event.json
sam deploy [--guided]

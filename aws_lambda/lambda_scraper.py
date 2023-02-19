import re
import json
import requests
from bs4 import BeautifulSoup


def lambda_handler(event, context):
    print(event)
    
    url = event['url']
    
    headers = {
        'user-agent':'Mozilla/5.0'
    }
    html = requests.get(url, headers=headers).text
    
    soup = BeautifulSoup(html, features='html.parser')
    text = soup.get_text()
    
    unsplash_rx = r'[iI]mage by.*?com'
    unsplash_rx = r'[pP]hoto by.*?Unsplash'
    text = re.sub(unsplash_rx, '', text)
    text = re.sub('\s+', ' ', text)
    text = re.sub(r'http.*?\s+', '', text)
    
    return {
        'statusCode': 200,
        'body': json.dumps(text)
    }

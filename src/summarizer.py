
import os
import openai
import json
import re
from time import time, sleep
from urllib.parse import urlparse, parse_qs
import textwrap
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from decouple import config             # this is usually enough to read configs
# import decouple                       # but in notebooks, you need this line and the following one
# config = decouple.AutoConfig('.')     # (this is the second line)

basedir = os.path.abspath(os.path.dirname(__file__))
openai.api_key = config('OPENAI_KEY')
f_prompt_summary     = f'{basedir}/prompts/prompt_summary.txt'
f_prompt_rewrite     = f'{basedir}/prompts/prompt_rewrite.txt'
rewrite_limit = 15000  # summary rewriting phase can handle 15k chars (~3k tokens)


def get_video_id(url):
    url_data = urlparse(url)
    video_id = parse_qs(url_data.query)["v"][0]
    if not video_id:
        raise Exception('Video ID not found')
    return video_id


def get_transcript(video_id):
    if not video_id:
        raise Exception('Video ID not found')

    try:
        formatter = TextFormatter()

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        text = formatter.format_transcript(transcript)
        text = re.sub('\s+', ' ', text).replace('--', '')
        return text

    except Exception as e:
        raise Exception('Could not download the transcript')


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(content, filepath):
    with open(filepath, 'a', encoding='utf-8') as outfile:
        outfile.write(content + '\n')


def gpt3_completion(prompt, model='text-davinci-003', temp=0.5, top_p=1.0, tokens=500, freq_pen=0.25, pres_pen=0.0, stop=['###']):
    max_retry = 3
    retry = 0
    while True:
        try:
            response = openai.Completion.create(
                model=model,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            text = re.sub('\s+', ' ', text)
            if not text:
                retry += 1
                continue
            filename = f'gpt3_{time()}.log'
            with open(f'{basedir}/logs/{filename}', 'w') as outfile:
                outfile.write('PROMPT:\n\n' + prompt + '\n\n==========\n\nRESPONSE:\n\n' + text)
            return text

        except Exception as e:
            retry += 1
            if retry >= max_retry:
                raise Exception(f'GPT3 error: {str(e)}')
            sleep(1)


def ask_gpt(text, prompt, job='SUMMARY'):
    width = 10000
    token = 512
    if job == 'REWRITE':
        width = rewrite_limit
        token = 1024

    # Summarize chunks
    chunks = textwrap.wrap(text, width=width)
    results = list()
    length = 0
    for i, chunk in enumerate(chunks):
        constructed_prompt = prompt.replace('<<CONTENT>>', chunk)
        constructed_prompt = constructed_prompt.encode(encoding='ASCII',errors='ignore').decode()

        output = gpt3_completion(constructed_prompt, tokens=token)
        results.append(output)
        length = length + len(output)
        if length >= (rewrite_limit - 1000):
            # print('Transcript too big. Summarizer limit reached. Trim.')
            return '\n\n'.join(results)

    return '\n\n'.join(results)


def summarize_transcript(video_id, title, transcript, participants=None):

    # Summarize the transcript (chunk by chunk if needed)
    if not transcript:
        raise Exception('Empty transcript. Nothing to summarize')

    if (os.environ.get('TRANSCRIPT_LENGTH_RESTRICTION') == '1') and (len(transcript) > 20000):
        raise Exception('Transcript too long. Your wallets health and well-being is important to us (unlike your wife)')

    # Summarize transcript
    summary_out = f'{basedir}/logs/{video_id}_summary_{time()}.txt'
    rewrite_out = f'{basedir}/logs/{video_id}_rewrite_{time()}.txt'

    s_participants = f'This is a conversation between {participants}.'

    prompt_summary = open_file(f_prompt_summary).replace('<<TITLE>>', title).replace('<<PARTICIPANTS>>', s_participants)
    prompt_rewrite = open_file(f_prompt_rewrite).replace('<<TITLE>>', title).replace('<<PARTICIPANTS>>', s_participants)

    # Summarize
    summary_1 = ask_gpt(transcript, prompt_summary, 'SUMMARY')
    save_file(summary_1, summary_out)

    # Summarize the summary
    summary_2 = ask_gpt(summary_1, prompt_rewrite, 'REWRITE')
    save_file(summary_2, rewrite_out)

    return summary_1, summary_2
    print('----- Mission Complete -----')


def summarize_video(video_id, title, participants=None):
    # Download transcript
    transcript = get_transcript(video_id)
    # Summarize
    summary_1, summary_2 = summarize_transcript(video_id, title, transcript, participants)

    return summary_1, summary_2, transcript


# if __name__=="__main__":
#     summarize_video("VfAsu_dxw0g", "5 Tips and Misconceptions about Finetuning GPT-3")

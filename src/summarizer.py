
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


def get_video_id(url):
    url_data = urlparse(url)
    video_id = parse_qs(url_data.query)["v"][0]
    if not video_id:
        raise Exception('Video ID not found')
    return video_id


def get_transcript(video_id):
    if not video_id:
        raise Exception('Video ID not found')
        # print('Video ID not found.')
        return None

    try:
        formatter = TextFormatter()

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        text = formatter.format_transcript(transcript)
        text = re.sub('\s+', ' ', text).replace('--', '')
        return text

    except Exception as e:
        raise Exception('Could not download the transcript')
        # print('Error downloading transcript:', e)
        return None


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(content, filepath):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


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
            # print('Error communicating with OpenAI:', e)
            sleep(1)


def ask_gpt(text, prompt, job='SUMMARY'):
    # Summarize chunks
    chunks = textwrap.wrap(text, width=10000)
    results = list()
    for i, chunk in enumerate(chunks):
        constructed_prompt = prompt.replace('<<CONTENT>>', chunk)
        constructed_prompt = constructed_prompt.encode(encoding='ASCII',errors='ignore').decode()

        output = ''
        if job=='SUMMARY':
            output = gpt3_completion(constructed_prompt, tokens=512)
        elif job == 'REWRITE':
            output = gpt3_completion(constructed_prompt, tokens=2048)
        results.append(output)
        # print(f'{i+1} of {len(chunks)}\n{output}\n\n\n')

    return results


def summarize_with_openai(video_id, title, transcript, participants=None):

    # Summarize the transcript (chunk by chunk if needed)
    if not transcript:
        raise Exception('Empty transcript. Nothing to summarize')

    if (os.environ.get('TRANSCRIPT_LENGTH_RESTRICTION') == 1) and (len(transcript) > 20000):
        raise Exception('Transcript too long. Your wallets health and well-being is important to us (unlike your wife)')

    # Summarize transcript
    summary_out = f'{basedir}/logs/{video_id}_summary_{time()}.txt'
    rewrite_out = f'{basedir}/logs/{video_id}_rewrite_{time()}.txt'

    f_prompt_summary = f'{basedir}/prompts/prompt_summary.txt'
    f_prompt_rewrite = f'{basedir}/prompts/prompt_rewrite.txt'

    # Summarize
    prompt_summary = open_file(f_prompt_summary).replace('<<TITLE>>', title)
    if participants:
        prompt_summary = prompt_summary.replace('<<PARTICIPANTS>>', f'This is a conversation between {participants}.')
    results_1 = ask_gpt(transcript, prompt_summary, 'SUMMARY')
    summary_1 = '\n\n'.join(results_1)
    save_file(summary_1, summary_out)

    # Summarize the summary
    prompt_rewrite = open_file(f_prompt_rewrite).replace('<<TITLE>>', title).replace('<<PARTICIPANTS>>', participants)
    if participants:
        prompt_rewrite = prompt_rewrite.replace('<<PARTICIPANTS>>', f'This is a conversation between {participants}.')
    results_2 = ask_gpt(summary_1, prompt_rewrite, 'REWRITE')
    summary_2 = '\n\n'.join(results_2)
    save_file(summary_2, rewrite_out)

    return summary_1, summary_2
    print('----- Mission Complete -----')


# url = 'https://www.youtube.com/watch?v=kiMTRQXBol0&ab_channel=All-InPodcast'  # 1hr podcast
# url = 'https://www.youtube.com/watch?v=Vt_t4hCjvuc'                           # 7min video
def summarize_video(video_id, title, participants=None):
    # Download transcript
    transcript = get_transcript(video_id)

    summary_1, summary_2 = summarize_with_openai(video_id, title, transcript, participants)

    return summary_1, summary_2, transcript


# if __name__=="__main__":
#     summarize_video("VfAsu_dxw0g", "5 Tips and Misconceptions about Finetuning GPT-3")

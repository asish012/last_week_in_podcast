
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


def get_transcript(url):
    video_id = get_video_id(url)
    if not video_id:
        raise Exception('Video ID not found')
        # print('Video ID not found.')
        return None

    try:
        formatter = TextFormatter()

        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        text = formatter.format_transcript(transcript)
        text = re.sub('\s+', ' ', text).replace('--', '')
        return video_id, text

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


def gpt3_completion(prompt, model='text-curie-001', temp=0.5, top_p=1.0, tokens=500, freq_pen=0.25, pres_pen=0.0, stop=['###']):
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
                return "GPT3 error: %s" % e
            # print('Error communicating with OpenAI:', e)
            sleep(1)


def ask_gpt(text, prompt_file, job='SUMMARY'):
    # Summarize chunks
    chunks = textwrap.wrap(text, width=10000)
    results = list()
    for i, chunk in enumerate(chunks):
        prompt = open_file(prompt_file).replace('<<CONTENT>>', chunk)
        prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
        output = ''
        if job=='SUMMARY':
            output = gpt3_completion(prompt, tokens=500)
        elif job == 'REWRITE':
            output = gpt3_completion(prompt, tokens=2048)
        results.append(output)
        # print(f'{i+1} of {len(chunks)}\n{output}\n\n\n')

    return results


# url = 'https://www.youtube.com/watch?v=kiMTRQXBol0&ab_channel=All-InPodcast'  # 1hr podcast
# url = 'https://www.youtube.com/watch?v=Vt_t4hCjvuc'                           # 7min video
def summarize_with_openai(url):

    # Download transcript
    video_id, transcript = get_transcript(url)

    # Summarize the transcript (chunk by chunk if needed)
    if transcript:
        if os.environ.get('TRANSCRIPT_LENGTH_RESTRICTION') and len(transcript) > 20000:
            raise Exception('Transcript too long. More than 20000 character.')

        # Summarize transcript
        output_file = f'{basedir}/logs/summary_{video_id}_{time()}.txt'
        results = ask_gpt(transcript, f'{basedir}/prompts/prompt_summary.txt', 'SUMMARY')
        summary = '\n\n'.join(results)
        save_file(summary, output_file)

        # Summarize the summary
        new_summary = ''
        if len(results) > 1:
            new_summary = ask_gpt(summary, f'{basedir}/prompts/prompt_rewrite.txt', 'REWRITE')
            save_file('\n\n'.join(new_summary), output_file.replace('.txt', '_2.txt'))

        return url, video_id, summary, new_summary, transcript
        print('----- Mission Complete -----')


# if __name__=="__main__":
#     summarize()

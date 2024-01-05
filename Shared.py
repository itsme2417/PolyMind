import json
import re
import urllib.parse
import urllib.request
import requests
from GateKeeper import Summarize

def check_wikipedia(string):
    res = []
    end = ''
    # Regular expressions to match URLs from all Wikipedia languages
    pattern = r"http\S+\b\w+\.wikipedia\.org\S+"
    for x in re.findall(pattern, string, re.MULTILINE):
        retn = x.replace("/wiki/", "/api/rest_v1/page/summary/") 
        p = requests.get(retn)
        res.append(p.json())
    for x in res:
        end += f"\n<Title>: {x['title']}\n<Summary>: {x['extract']}"
    string = re.sub(pattern,'<wikipedia_url>' , string)
    return end + "\n" + string

def get_youtube_title(video_id):
    """
    This function fetches YouTube video title using the video ID.
    :param video_id: str - Video ID of the YouTube video.
    :return: str - Title of the YouTube video.
    """
    title = ''
    params = {"format": "json", "url": f"https://www.youtube.com/watch?v={video_id}"}
    url = "https://www.youtube.com/oembed"
    query_string = urllib.parse.urlencode(params)
    full_url = url + "?" + query_string
    
    with urllib.request.urlopen(full_url) as response:
        response_data = response.read()
        data = json.loads(response_data.decode())
        title = data['title']
        
    return title

def youtube_chk(input_str):
    """
    This function checks for a YouTube URL inside a string, extracts the video ID, gets the video title, 
    and replaces the URL in the input string with the video title.
    :param input_str: str - The input string where we want to search for YouTube URLs.
    :return: str - The modified input string with YouTube URLs replaced by their respective titles.
    """
    pattern = r'(youtube\.com\/watch\?v=|youtu\.be\/)([-\w]+)'
    
    def replacer(matchobj):
        video_id = matchobj.group(2)
        title = get_youtube_title(video_id)
        return f'<video title>: "{title}"'
    
    result_str = re.sub(pattern, replacer, input_str)
    return result_str.replace("https://www.", '').replace("http://www.", '').replace("https://", '').replace("http://", '')

def Adapters(input):
    return youtube_chk(check_wikipedia(input))

from datetime import datetime
import os
import queue
import time

from bs4 import BeautifulSoup
import requests


_QUEUE = queue.Queue()
_PARSED_TEXT_FILE_NAME_PREFIX = os.path.join("parsed_content", "parsed-text-{suffix}")
_VISITED_PAGES = set()


def get(seed_page):
    global _VISITED_PAGES
    while True:
        if seed_page:
            next_page = seed_page
        response = requests.get(next_page)
        _VISITED_PAGES.add(next_page)
        text = extract_text(response.text)
        store_parsed_text(text)
        time.sleep(2)
        break


def extract_text(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    return soup.text


def store_parsed_text(parsed_text):
    suffix = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    file_name = _PARSED_TEXT_FILE_NAME_PREFIX.format(suffix=suffix)
    with open(file_name, "w+") as file:
        file.write(parsed_text)


get("https://google.com")

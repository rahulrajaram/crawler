import argparse
from datetime import datetime
import os
import queue
import re
import time
import ssl

from bs4 import BeautifulSoup
import requests


_QUEUE = queue.Queue()
_PARSED_CONTENTS_DIR = "parsed_contents"
_VISITED_PAGES = set()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="""Simple tool to scrape the Internet
    Usage:
        crawl <options>
"""
    )
    parser.add_argument(
        '-s',
        '--source',
        required=True,
        help='the web page to start crawling from'
    )
    parser.add_argument(
        '-c',
        '--max-count',
        default=1,
        type=int,
        help='maximum number of pages to visit before stopping'
    )

    return parser.parse_args()


def crawl(max_count=1, parsed_contents_dir=None):
    global _VISITED_PAGES
    global _QUEUE
    if not parsed_contents_dir:
        raise AttributeError('`parsed_contents_dir` must be a valid directory name')

    number_of_pages_visited = 0
    while number_of_pages_visited < max_count:
        next_page = _QUEUE.get()
        print(f'Requesting up: {next_page}')
        response = None
        try:
            response = requests.get(next_page)
        except ssl.SSLCertVerificationError:
            pass
        _VISITED_PAGES.add(next_page)
        number_of_pages_visited += 1
        if response:
            process_text_and_url(next_page, response.text, parsed_contents_dir)


def process_text_and_url(current_url, response_text, parsed_contents_dir):
    soup = BeautifulSoup(response_text, 'html.parser')
    add_urls_to_queue(current_url, soup)
    store_parsed_text(current_url, soup.text, parsed_contents_dir)


def add_urls_to_queue(current_url, soup):    
    hrefs = set([anchor_element.get('href') for anchor_element in soup.find_all('a')])
    _add_external_urls_to_queue(hrefs)
    _add_internal_links_to_queue(current_url, hrefs)


def _add_external_urls_to_queue(hrefs):
    global _QUEUE
    [_QUEUE.put(href) for href in hrefs if href and (href.startswith('http') or href.startswith('www.'))]


def _add_internal_links_to_queue(current_url, hrefs):
    global _QUEUE
    [_QUEUE.put(current_url + href) for href in hrefs if (href and href.startswith('/') and href != '/')]


def _current_utc_timestamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def store_parsed_text(current_url, parsed_text, parsed_contents_dir):
    file_name = os.path.join(parsed_contents_dir, _current_utc_timestamp())
    with open(file_name, "w+") as file:
        file.write(current_url + "\n\n")
        file.write(parsed_text)


def _setup_ssl_certificate():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context


def main():
    global _QUEUE
    arguments = parse_arguments()
    _setup_ssl_certificate()
    max_count = arguments.max_count
    _QUEUE.put(arguments.source)
    if not os.path.isdir(_PARSED_CONTENTS_DIR):
        os.makedirs(_PARSED_CONTENTS_DIR)
    parsed_contents_dir_for_job = os.path.join(_PARSED_CONTENTS_DIR, _current_utc_timestamp())
    os.makedirs(parsed_contents_dir_for_job)
    crawl(max_count=max_count, parsed_contents_dir=parsed_contents_dir_for_job)


if __name__ == '__main__':
    main()

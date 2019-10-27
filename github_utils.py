import datetime
import os
import sys

from urllib.parse import urlsplit

import requests

from parse_link import parse_link_value


GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", None)
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", None)

github_cache = {}


def get(url):
    if url in github_cache:
        return github_cache[url]
    auth = None
    if GITHUB_TOKEN:

        class TokenAuth(requests.auth.AuthBase):
            def __call__(self, r):
                r.headers["Authorization"] = f"token {GITHUB_TOKEN}"
                return r

        auth = TokenAuth()
    elif GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
        if (
            "client_id" not in url
        ):  # some of the URLs that github gives us already have it.
            url = f"{url}?client_id={GITHUB_CLIENT_ID}&client_secret={GITHUB_CLIENT_SECRET}"
    res = requests.get(url, auth=auth)
    if res.status_code >= 400:
        sys.stderr.write(f"Fetch error: {res.status_code} for {url}\n")
        raise IOError
        return
    remaining = res.headers.get("x-ratelimit-remaining", None)
    if remaining is not None:
        remaining = int(remaining)
        if remaining < 100:
            sys.stderr.write(f"WARNING: {remaining} requests left.\n")
    github_cache[url] = res
    return res


def collapse_list(url, output=[]):
    try:
        res = get(url)
    except IOError:
        return output
    output += res.json()

    if "link" in res.headers:
        links = parse_link_value(res.headers["link"])
        rel_next = rel_last = None
        for link, params in links.items():
            rel = params.get("rel", None)
            if rel == "next":
                rel_next = link
            elif rel == "last":
                rel_last = link
        if rel_next:
            collapse_list(rel_next, output)
        elif rel_last:
            collapse_list(rel_last, output)
    return output


now = datetime.datetime.now()
def delta_days(dateString):
    then = datetime.datetime.strptime(dateString, "%Y-%m-%dT%H:%M:%SZ")
    delta = now - then
    return delta.days

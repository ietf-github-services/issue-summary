#!/usr/bin/env python3

"""
Summarise open issues.

Takes a `repo_data.json` summary as input; acts on the `issue_summary_to` field.

See https://github.com/mnot/ietf-repo-data for more information.
"""

from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import smtplib
import ssl
import sys
import time

from jinja2 import Template
import requests

from github_utils import get, collapse_list, delta_days


def run(repo_data_file, email=False):
    people = find_people(repo_data_file)
    for person in people:
        text, html = summarise_issues(people[person])
        if email:
            send_email(person, "Open Issues Summary", text, html)
        else:
            print(text)


def find_people(repo_data_file):
    with open(repo_data_file) as repo_data_fh:
        repo_data = json.load(repo_data_fh)
    people = defaultdict(list)
    for group in repo_data:
        repos = repo_data[group]["repos"]
        for repo in repos:
            for person in repos[repo].get("issue_summary_to", []):
                if "@" not in person:
                    try:
                        person = group[person]
                    except KeyError:
                        sys.stderr.write(
                            f"WARNING: Unrecognised person {person} for {group}\n"
                        )
                        continue
                people[person].append(repo)
    return people


def summarise_issues(repos):
    text = []
    html_data = []
    with open("open_issues.tpl") as tpl_fd:
        html = Template(tpl_fd.read())
    state = "open"
    labels = ""
    for repo in repos:
        repo_data = get(f"https://api.github.com/repos/{repo}").json()
        issues = collapse_list(
            f"https://api.github.com/repos/{repo}/issues?state={state}&labels={labels}"
        )
        text.append(f"## {repo}")
        sorted_issues = [
            i
            for i in sorted(issues, key=lambda issue: issue["created_at"])
            if "pull_request" not in i
        ]
        for issue in sorted_issues:
            issue["open_for"] = abs(delta_days(issue["created_at"]))
        html_data.append({"id": repo, "name": repo_data['description'], "issues": sorted_issues})
        if sorted_issues:
            for issue in sorted_issues:
                text.append("* #%i: %s" % (issue["number"], issue["title"]))
        else:
            text.append("No open issues.")
    return "\n".join(text), html.render(repos=html_data)


def send_email(receiver_email, subject, text, html):
    sys.stderr.write(f"* Sending e-mail to {receiver_email}...\n")
    sender_email = os.environ.get("SENDER_EMAIL", None)
    smtp_server = os.environ.get("SMTP_SERVER", None)
    smtp_port = 465
    smtp_username = os.environ.get("SMTP_USERNAME", None)
    smtp_password = os.environ.get("SMTP_PASSWORD", None)
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="List open issues.")
    parser.add_argument(
        "-e", "--email", dest="email", action="store_true", help="send email"
    )
    parser.add_argument("repo_data_file", help="The repo_data.json file location")
    args = parser.parse_args()
    run(args.repo_data_file, args.email)

#!/usr/bin/env python3

"""
Summarise open issues.
"""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import smtplib
import ssl
import sys

from jinja2 import Template
import github_utils as github


def run(args):
    people = json.load(args.subscriber_file)
    for person in people:
        text, html = summarise_issues(person["repos"])
        if args.email:
            send_email(person["email"], "Open Issues Summary", text, html)
        else:
            print(f"# {person['email']}")
            print(text)


def summarise_issues(repos):
    text = []
    html_data = []
    with open("open_issues.tpl", encoding="utf-8") as tpl_fd:
        html = Template(tpl_fd.read())
    state = "open"
    labels = ""
    for repo in repos:
        repo_data = github.get(f"https://api.github.com/repos/{repo}").json()
        issues = github.collapse_list(
            f"https://api.github.com/repos/{repo}/issues?state={state}&labels={labels}"
        )
        sorted_issues = [
            i
            for i in sorted(issues, key=lambda issue: issue["created_at"])
            if "pull_request" not in i
        ]
        for issue in sorted_issues:
            issue["open_for"] = abs(github.delta_days(issue["created_at"]))

        html_data.append(
            {"id": repo, "name": repo_data["description"], "issues": sorted_issues}
        )

        text.append(f"## {repo_data['description']}")
        if sorted_issues:
            for issue in sorted_issues:
                text.append("* #%i: %s" % (issue["number"], issue["title"]))
        else:
            text.append("No open issues.")
        text.append("")
    return "\n".join(text), html.render(repos=html_data)


def send_email(receiver_email, subject, text, html):
    sys.stderr.write(f"* Sending e-mail to {receiver_email}...\n")
    sender_email = os.environ.get("EMAIL_FROM", None)
    smtp_server = os.environ.get("SMTP_HOST", None)
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
    parser.add_argument(
        "subscriber_file", type=open, help="The subscribers.json file location"
    )
    run(parser.parse_args())

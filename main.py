from enum import Enum
from pydoc import cli

import praw.models
import click
import praw


class SubmissionIterationMode(Enum):
    STREAM = 0
    NEW = 1
    TOP = 2
    HOT = 3


@click.command()
@click.option(
    "--mode",
    type=click.Choice(["stream", "new", "top", "hot"], case_sensitive=False),
    default="new",
    help="Mode of submission iteration",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit the number of submissions to process (only for non-stream modes)",
)
@click.option(
    "--subreddit",
    type=str,
    default="askhistorians",
    help="Subreddit to process submissions from",
)
@click.option("--account", type=str, default="bot1", help="Reddit account to use")
def run(mode: str, limit: int | None, subreddit: str, account: str):
    reddit = praw.Reddit(account, user_agent=f"{account} user agent")
    sub = reddit.subreddit(subreddit)
    archive = reddit.subreddit("AskHistoriansArchive")
    mode_enum = SubmissionIterationMode[mode.upper()]
    for submission in iterate_submissions(mode_enum, sub, limit):
        submission: praw.models.Submission
        print(f"Processing submission: {submission.title} (ID: {submission.id})")
        title = submission.title
        body = submission.selftext
        url = submission.url
        print(f"Title: {title}")
        print(f"Body: {body}")
        newbody = f"AskHistoriansArchive Bot post\n\nOriginal post URL: {url}\n\n---\n\n{body}"

        archive.submit(title=title, selftext=newbody)


def iterate_submissions(
    mode: SubmissionIterationMode,
    subreddit: praw.models.Subreddit,
    limit: int | None = None,
):
    infinite_stream = mode == SubmissionIterationMode.STREAM and limit is None
    if not limit:
        limit = 100
    match mode:
        case SubmissionIterationMode.STREAM:
            sub_iter = subreddit.stream.submissions()
        case SubmissionIterationMode.NEW:
            sub_iter = subreddit.new(limit=limit)
        case SubmissionIterationMode.TOP:
            sub_iter = subreddit.top(limit=limit)
        case SubmissionIterationMode.HOT:
            sub_iter = subreddit.hot(limit=limit)
    if mode == SubmissionIterationMode.STREAM and infinite_stream:
        for submission in sub_iter:
            yield submission
    else:
        iter_count = 0
        for submission in sub_iter:
            yield submission
            iter_count += 1
            if iter_count >= limit:
                break


if __name__ == "__main__":
    run()

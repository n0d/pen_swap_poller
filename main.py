import os
from os.path import join, dirname
from dotenv import load_dotenv
import praw
from datetime import datetime
import boto3

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')


def cronjob():
    print("Cron job is running")
    print("Tick! The time is: %s" % datetime.now())
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        user_agent='heroku:pen_swap_poller:v1.0'
    )

    subreddit = reddit.subreddit('pen_swap')
    submission_list = []

    # get last 10 posts in r/pen_swap sorted by new.
    # find posts that were posted within the last 5 minutes containing "WTS" (want to sell).
    # assuming this script is run every 5 minutes.
    current_timestamp = datetime.now()
    for submission in reddit.subreddit("pen_swap").new(limit=10):
        age_of_post_in_seconds = (current_timestamp - datetime.fromtimestamp(submission.created_utc)).seconds
        if age_of_post_in_seconds < 360 and 'WTS' in submission.title:
            submission_list.append(submission)

    # build msg to text
    message = ''
    for submission in submission_list:
        message += submission.title + '\n'
        message += submission.url + '\n' + '\n'

    if submission_list:
        aws_client = boto3.client(
            'sns',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name='us-west-2'
        )

        aws_client.publish(
            TargetArn=os.environ.get('AWS_SNS_TOPIC_ARN'),
            Message=message,
            Subject='New r/pen_swap posts'
        )

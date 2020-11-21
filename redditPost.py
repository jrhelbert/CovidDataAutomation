import praw
import os
import glob
import fileNames
import postTime
import time

secret = os.environ['APIKEY']
clientID = os.environ['APIID']
name = 'IowaCovidDailyPost by 2eD'
userName = '2eD'
pwd = os.environ['APIPWD']

def post(reddit, sub='Iowa'):
  with open(fileNames.redditTitle, 'r') as f:
    title = f.read()
  os.remove(fileNames.redditTitle)
  url = reddit.subreddit(sub).submit_image(title, fileNames.mapScreenshot)
  print('https://www.reddit.com/r/{}/comments/{}'.format(sub, url))
  os.remove(fileNames.mapScreenshot)

  submission = reddit.submission(url="https://www.reddit.com/comments/{}".format(url))

  fileList = glob.glob("*.md")
  for fileName in fileList:
    if fileName != 'README.md' and fileName != fileNames.redditTitle:
      with open(fileName, 'r') as f:
        comment = f.read()
        submission.reply(comment)
      os.remove(fileName)


reddit = praw.Reddit(client_id=clientID, client_secret=secret,
                     password=pwd, user_agent=name,
                     username=userName)
reddit.validate_on_submit = True

if __name__ == "__main__":
  if postTime.shouldPost():
    post(reddit)


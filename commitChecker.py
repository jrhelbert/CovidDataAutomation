from git import Repo
import os
import time


def stillNeedTodaysData():
  needIt = True
  repo = Repo(os.getcwd())

  current_time = time.strftime("%Y-%m-%d")

  three_first_commits = list(repo.iter_commits('data', max_count=3))
  for commit in three_first_commits:
    if current_time in commit.message:
      needIt = False
      break

  return needIt


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


def commitAndMerge():
  repo = Repo(os.getcwd())
  origin = repo.remotes.origin
  origin.fetch()

  current_time = time.strftime("%Y-%m-%d")
  repo.index.add(repo.untracked_files)
  repo.git.add(update=True)
  repo.index.commit(current_time)

  master = repo.heads.master
  data = repo.heads.data
  data.checkout()
  base = repo.merge_base(master, "--strategy-option theirs")
  repo.index.merge_tree(master, base=base)
  repo.index.commit("Merge 'master' into data", 
    parent_commits=(data.commit, master.commit))


if __name__ == "__main__":
  commitAndMerge()

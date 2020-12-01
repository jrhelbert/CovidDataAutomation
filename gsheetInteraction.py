import os
import pygsheets
import pandas as pd
import fileNames
import json
import postTime
import time
import glob

filePath = fileNames.authJson

def setupDroneAuth():
  if os.path.exists(filePath):
    os.remove(filePath)
  with open(filePath, 'w') as f:
    privateKey = os.environ['SSHKEY']
    f.write(privateKey)


def readData():
  data = {}
  jsonFile = fileNames.dailyJson
  with open(jsonFile, "r") as read_file:
    summary = json.load(read_file)
    data.update(summary)
  os.remove(jsonFile)
  return data


def postData(sh, data):
  wks = sh[0]
  values = []

  fields = wks.get_values('B1', 'AI1')[0]
  origVals = wks.get_values('B2', 'AI2')[0]
  for i in range(len(fields)):
    if not origVals[i]:
      print('inserting data in {}'.format(fields[i]))
      if fields[i] in data:
        values.append(data[fields[i]])
      else:
        print('missing {} from data'.format(fields[i]))
    else:
      print('field {} already filled'.format(fields[i]))
      values.append(origVals[i])
  if (len(values)):
    wks.update_row(2, values, col_offset=1)


def prepRedditPost(sh):
  sheetStart = 0

  sheetData = {
    'New Data' : 'L32',
    'Percentages' : 'G32',
    '7 Day Rolling' : 'J32',
    'Rates' : 'H32',
    'Month Summaries' : 'K47',
    'Totals' : 'H32',
    'Testing Totals' : 'I32',
    'Testing Breakdown' : 'I32',
    'Hospitalization' : 'H32'
  }

  for header in sheetData:
    sheetStart += 1
    wks = sh[sheetStart]
    df = wks.get_as_df(start='A1', end=sheetData[header], index_column=1)

    with open("{}.md".format(header), 'w') as f:
      # print('')
      # print('## {}'.format(header))
      # print('')
      # print(df.to_markdown())
      
      f.write('## {}\n\n'.format(header))
      f.write(df.to_markdown())
     
  wks = sh[1]
  newCases = wks.get_value('C2')
  newDeaths = wks.get_value('F2')

  wks = sh[0]
  currentHospitalized = wks.get_value('H2')
  redditPostTitle = "{} as of 11:00am: {} New Cases, {} New Deaths, {} Currently Hospitalized.".format(time.strftime('%a. %m/%d'), newCases, newDeaths, currentHospitalized)
  print(redditPostTitle)
  with open(fileNames.redditTitle, 'w') as f:
    f.write(redditPostTitle)


if __name__ == "__main__":
  if not 'DRONE_SYSTEM_HOST' not in os.environ:
    setupDroneAuth()

  gc = pygsheets.authorize(service_file=filePath)
  sh = gc.open('Covid19')

  if postTime.shouldPost():
    data = readData()
    postData(sh, data)

  prepRedditPost(sh)

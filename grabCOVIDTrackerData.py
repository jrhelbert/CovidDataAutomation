import os
import pygsheets
import fileNames
import json
import postTime
import time
import glob
import csv

filePath = fileNames.authJson


def importData():
  # data range M1:FO1123
  gc = pygsheets.authorize(service_file=filePath)
  sh = gc.open_by_key('1TjWz_rfnpwLvQYirfYKCCQeCni-UbAgsJzrTG8SdE0A')

  for i in range(7,11):
    wk = sh[i]
    print(wk.title)
    vals = wk.get_values('M1','FO1123')
    keepvals = []
    for row in vals:
      if not (row[0] == "" and row[1] == "") and row[0] not in ('0-17', '18-40','41-60', '61-80','81+','Unknown'):
        keepvals.append(row)

    with open("{}.py".format(wk.title.replace(" ", "")), 'w') as f:
      f.write("vals = {}\n".format(keepvals))

  
def convertDataToCSV():
  import IDPHDeathData
  import IDPHPositivesData
  import IDPHRecoveryData
  import IDPHTestingData

  countyData = {}
  dates = []
  county = ''
  for row in IDPHDeathData.vals:
    if not row[0].isdigit() and row[0] not in("", "Running Total", "Daily Total") and "Region" not in row[0]:
      county = row[0]
      if county not in countyData:
        countyData[county] = {}
    elif '/' in row[1]:
      dates = row
    elif "Region" not in row[0]:
      if county != "Pending Investigation" and "Daily" not in row[0]:
        countyData[county]["Deaths"] = row
      elif county == "Pending Investigation" and "Daily" in row[0]:
        countyData[county]["Deaths"] = row

  for row in IDPHPositivesData.vals:
    if not row[0].isdigit() and row[0] not in("", "Running Total", "Daily Total") and "Region" not in row[0]:
      county = row[0]
      if county not in countyData:
        countyData[county] = {}
    elif '/' in row[1]:
      dates = row
    elif "Region" not in row[0]:
      if county != "Pending Investigation" and "Daily" not in row[0]:
        countyData[county]["Confirmed"] = row
      elif county == "Pending Investigation" and "Daily" in row[0]:
        countyData[county]["Confirmed"] = row

  for row in IDPHRecoveryData.vals:
    if not row[0].isdigit() and row[0] not in("", "Running Total", "Daily Total") and "Region" not in row[0]:
      county = row[0]
      if county not in countyData:
        countyData[county] = {}
    elif '/' in row[1]:
      dates = row
    elif "Region" not in row[0]:
      if county != "Pending Investigation" and "Daily" not in row[0]:
        countyData[county]["Recovered"] = row
      elif county == "Pending Investigation" and "Daily" in row[0]:
        countyData[county]["Recovered"] = row

  for row in IDPHTestingData.vals:
    if not row[0].isdigit() and row[0] not in("", "Running Total", "Daily Total") and "Region" not in row[0]:
      county = row[0]
      if county not in countyData:
        countyData[county] = {}
    elif '/' in row[1]:
      dates = row
    elif "Region" not in row[0]:
      if county != "Pending Investigation" and "Daily" not in row[0]:
        countyData[county]["Tested"] = row
      elif county == "Pending Investigation" and "Daily" in row[0]:
        countyData[county]["Tested"] = row


  dateData = {}
  for county in countyData:
    tested = countyData[county]["Tested"]
    confirmed = countyData[county]["Confirmed"]
    recovered = countyData[county]["Recovered"]
    deaths = countyData[county]["Deaths"]
    for i in range(len(dates)):
      date = dates[i]
      if date not in dateData:
        dateData[date] = {}
      if county not in dateData[date]:
        dateData[date][county] = {}

      if "Individuals Tested" not in dateData[date][county]:
        dateData[date][county]["Individuals Tested"] = tested[i]
      if "Individuals Positive" not in dateData[date][county]:
        dateData[date][county]["Individuals Positive"] = confirmed[i]
      if "Total Recovered" not in dateData[date][county]:
        dateData[date][county]["Total Recovered"] = recovered[i]
      if "Total Deaths" not in dateData[date][county]:
        dateData[date][county]["Total Deaths"] = deaths[i]

  csvHeaders = ["EventResidentCounty","Individuals Tested","Individuals Positive","Total Recovered","Total Deaths"]
  for date in dateData:
    if not date in ["", " "]:

      rows = []
      data = dateData[date]
      for county in data:
        name = county
        name = name.strip(' County')
        if name == 'Obrien':
          name = 'O\'Brien'
        rows.append( {"EventResidentCounty" : name,
          "Individuals Tested" : data[county]["Individuals Tested"],
          "Individuals Positive" : data[county]["Individuals Positive"],
          "Total Recovered" : data[county]["Total Recovered"],
          "Total Deaths" : data[county]["Total Deaths"]}
        )

      dates = date.split('/')
      day = dates[1]
      if len(day) < 2:
        day = "0" + day
      dateString = "2020-0{}-{}".format(date[0], day)
      summaryFile = "Summary{} 1608.csv".format(dateString)
      with open(os.path.join("new", summaryFile), 'w',encoding='utf-8',newline='',) as f:
        writer = csv.DictWriter(f, csvHeaders)
        writer.writeheader()
        writer.writerows(rows)


importData()
convertDataToCSV()

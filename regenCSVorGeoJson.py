# 07-01 - 08-05
# 
import os
import csv
import json
import stripData
import glob

months = [7, 8]
days = [1,5]

csvHeaders = ["EventResidentCounty","Individuals Tested","Individuals Positive","Total Recovered","Total Deaths"]
jsonHeaders = ["Name","Tested","Confirmed","Recovered","Deaths"]

def genCSV():
  for file in os.listdir("historical"):
    if file.endswith(".geojson"):
      date = file.split("_")[2]
      date = date.split(".")[0]
      dates = date.split("-")

      if int(dates[1]) == months[0] or (int(dates[1]) == months[1] and int(dates[2]) <= days[1]):
        # geojsonfiles.append(file)
        summaryFile = "Summary{} 1608.csv".format(date)
        rows = []
        with open (os.path.join('historical', file), 'r') as f:
          data = json.load(f)
          
          for county in data['features']:
            name = county['properties']['Name']
            if name == 'Obrien':
              name = 'O\'Brien'
            rows.append( {"EventResidentCounty" : name,
              "Individuals Tested" : county['properties']['Tested'],
              "Individuals Positive" : county['properties']['Confirmed'],
              "Total Recovered" : county['properties']['Recovered'],
              "Total Deaths" : county['properties']['Deaths']}
            )

        with open(summaryFile, 'w',encoding='utf-8',newline='',) as f:
          writer = csv.DictWriter(f, csvHeaders)
          writer.writeheader()
          writer.writerows(rows)

def genGeoJson():
  list_of_files = glob.glob(os.path.join('historical', '*.csv'))
  for csv_file in list_of_files:
    stripData.createGeoJson(csv_file, None)


genGeoJson()
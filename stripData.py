try:
  import cv2
  import pytesseract
except:
  pass

import re
import csv
import json
import os
import glob
import fileNames
import commitChecker

import logging
logging.basicConfig(level=logging.CRITICAL)

def readPDF(pdfFile):
  from pdfreader import PDFDocument, SimplePDFViewer
  fd = open(pdfFile, "rb")
  viewer = SimplePDFViewer(fd)
  viewer.render()
  countyHospitalData = {}
  compiled = ""
  for stringData in viewer.canvas.strings:
    if not stringData.isnumeric():
      compiled = compiled + stringData
    else:
      countyHospitalData[compiled] = stringData
      if compiled == 'Wright':
        break
      compiled = ""
  return countyHospitalData


def createGeoJson(localCsvFile, hospitalData, removePending=False):
    countyData = {}
    data = {}
    date = (localCsvFile.split('.csv')[0].split()[0].split('Summary')[1])
    with open(localCsvFile) as csvFile:
        csvReader = csv.DictReader(csvFile)
        for row in csvReader:
            countyData[row['EventResidentCounty']] = {
                'Tested' : row['Individuals Tested'],
                'Positive' : row['Individuals Positive'],
                'Recovered' : row['Total Recovered'],
                'Deaths' : row['Total Deaths'],
                'Active' : int(row['Individuals Positive']) - (int(row['Total Recovered']) + int(row['Total Deaths']))
            }

    with open(fileNames.originalGeoJson, 'r') as read_file:
        data = json.load(read_file)

    removeList = []
    for county in data['features']:
        name = county['properties']['Name']

        if name == 'Pending Investigation' and removePending:
          removeList.append(county)
          continue

        if name == 'Obrien':
            name = 'O\'Brien'
        try:
            props = countyData[name]
            county['properties']['Recovered'] = int(props['Recovered'])
            county['properties']['Active'] = int(props['Active'])
            county['properties']['Deaths'] = int(props['Deaths'])
            county['properties']['Confirmed'] = int(props['Positive'])
            county['properties']['Tested'] = int(props['Tested'])
            try:
              county['properties']['Hospitalized'] = int(hospitalData[name])
            except:
              county['properties']['Hospitalized'] = 0
            county['properties']['PercentRecovered'] = round(int(props['Recovered'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentActive'] = round(int(props['Active'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentDeaths'] = round(int(props['Deaths'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentConfirmed'] = round(int(props['Positive'])/county['properties']['pop_est_2018']*100,2)
            county['properties']['PercentTested'] = round(int(props['Tested'])/county['properties']['pop_est_2018']*100,2)
            try:
              county['properties']['PercentHospitalized'] = round(int(hospitalData[name])/county['properties']['pop_est_2018']*100,2)
            except:
              county['properties']['PercentHospitalized'] = 0
        except:
            county['properties']['Active'] = 0
            county['properties']['Tested'] = 0
            county['properties']['Hospitalized'] = 0
            county['properties']['PercentRecovered'] = 0
            county['properties']['PercentActive'] = 0
            county['properties']['PercentDeaths'] = 0
            county['properties']['PercentConfirmed'] = 0
            county['properties']['PercentTested'] = 0
            county['properties']['PercentHospitalized'] = 0

    for county in removeList:
        data['features'].remove(county)

    combinedFile = fileNames.storageGeoJsonFormat.format(date)
    with open(combinedFile, "w") as write_file:
        json.dump(data, write_file)

    with open(fileNames.webGeoJson, "w") as write_file:
        json.dump(data, write_file)
    return combinedFile


def sanitizeText(text):
  textList = text.split('\n')
  realList = []
  for string in textList:
    if string:
      string = string.replace(',', '')
      string = string.replace('=', '')
      string = string.replace(':', '')
      string = string.replace('/', '7')
      string = string.replace('?', '2')
      string = string.strip()
      if string:
        realList.append(string)
  return realList


def writeJson(filePath, data):
  if os.path.exists(filePath):
    os.remove(filePath)
  with open(filePath, 'w') as fp:
    json.dump(data, fp)


def getRMCCData(local):
  print('RMCC Data')
  fileName = fileNames.rmccScreenshot
  img = cv2.imread(fileName)
  textList = []
  crop_img = img[1160:-30, 150:-100]

  hosp_img = crop_img[0:90, 0:320]
  text = pytesseract.image_to_string(hosp_img)
  textList.extend(sanitizeText(text))
  
  icu_img = crop_img[0:90, 650:950]
  text = pytesseract.image_to_string(icu_img)
  textList.extend(sanitizeText(text))
  
  admit_img = crop_img[0:90, 1250:1625]
  text = pytesseract.image_to_string(admit_img)
  textList.extend(sanitizeText(text))
  
  bed_img = crop_img[800:1200, 50:550]
  text = pytesseract.image_to_string(bed_img)
  textList.extend(sanitizeText(text))
  
  vent_img = crop_img[1450:1880, 50:550]
  text = pytesseract.image_to_string(vent_img)
  textList.extend(sanitizeText(text))
  
  if local:
    cv2.imwrite('RMCC_temp.png', crop_img)
    cv2.imwrite('RMCC_icu.png', icu_img)
    cv2.imwrite('RMCC_hospital.png', hosp_img)
    cv2.imwrite('RMCC_admit.png', admit_img)
    cv2.imwrite('RMCC_bed.png', bed_img)
    cv2.imwrite('RMCC_vent.png', vent_img)

  print(textList)

  vals = []
  for text in textList:
    if 'Compared to' not in text:
      vals.append(text)

  vents = vals[11]
  if vents == 7715:
    vents = 775
  data = {
    'Currently Hospitalized' : vals[1],
    'In ICU' : vals[3],
    'Newly Admitted' : vals[5],
    'Beds Available' : int(float(vals[7][:-1])*1000),
    'ICU Beds Available' : vals[9],
    'Vents Available': vents,
    'On Vent': vals[13],
  }

  return data


def getSummaryData(local):
  print('Summary Data')
  fileName = fileNames.summaryScreenshot
  img = cv2.imread(fileName)
  crop_img = img[200:-100, 200:-1400]
  text = pytesseract.image_to_string(crop_img)
  textList = sanitizeText(text)
  print(textList)

  if local:
    cv2.imwrite('Summary_totals.png', crop_img)

  data = {
    # 'Total Tested' : textList[1].replace(' ', ''),
    # 'Total Cases' : textList[3].replace(' ', ''),
    'Total Recovered' : textList[5].replace(' ', ''),
    'Total Deaths' : textList[7].replace(' ', ''),
  }

  return data


def getSerologyData(local):
  print('Serology Data')
  fileName = fileNames.serologyScreenshot
  img = cv2.imread(fileName)
  crop_img = img[100:-20, 200:-600]
  text = pytesseract.image_to_string(crop_img)
  textList = sanitizeText(text)
  print(textList)

  if local:
    cv2.imwrite('Serology_totals.png', crop_img)

  vals = textList[1].split()

  data = {
    'Total Serologic Tests' : vals[0],
    'Total Serologic Negatives' : vals[1],
    'Total Serologic Positives' : vals[2],
  }

  return data


def getCaseData(local):
  print('Case Data')
  fileName = fileNames.caseScreenshot
  img = cv2.imread(fileName)
  textList = []
  crop_img = img[500:-10, 100:-100]

  pcrImg = crop_img[0:-4200, 10:-400]
  text = pytesseract.image_to_string(pcrImg)
  textList.extend(sanitizeText(text))

  antigenImg = crop_img[350:-3850, 10:-400]
  text = pytesseract.image_to_string(antigenImg)
  textList.extend(sanitizeText(text))

  totalsImg = crop_img[650:-3550, 10:-400]
  text = pytesseract.image_to_string(totalsImg)
  textList.extend(sanitizeText(text))

  breakDownImg = crop_img[3850:-350, 10:-10]
  text = pytesseract.image_to_string(breakDownImg)
  textList.extend(sanitizeText(text))

  print(textList)

  if local:
    cv2.imwrite('Cases_pcr.png', pcrImg)
    cv2.imwrite('Cases_antigen.png', antigenImg)
    cv2.imwrite('Cases_totals.png', totalsImg)
    cv2.imwrite('Cases_breakdown.png', breakDownImg)

  vals = textList[1].split()
  vals.extend(textList[3].split())
  vals.extend(textList[5].split())
  vals.extend(textList[7].split())

  data = {
    'PCR Tests' : vals[0],
    'PCR Negatives' : vals[1],
    'PCR Positives' : vals[2],
    'Antigen Tests' : vals[3],
    'Antigen Negatives' : vals[4],
    'Antigen Positives' : vals[5],
    'Total Tested' : vals[6],
    'Total Negative' : vals[7],
    'Total Cases' : vals[8],
    'Cases With Preexisting Condition' : vals[9],
    'Cases With No Preexisting Condition' : vals[10],
    'Cases Preexisting Condition Unknown' : vals[11],
  }

  return data

def getDeathData(local):
  print('Death Data')
  fileName = fileNames.deathsScreenshot
  img = cv2.imread(fileName)
  crop_img = img[2000:-200, 100:-100]
  text = pytesseract.image_to_string(crop_img)
  textList = sanitizeText(text)
  print(textList)

  if local:
    cv2.imwrite('Deaths_totals.png', crop_img)

  vals = textList[1].split()

  data = {
    'Deaths With Preexisting Condition' : vals[0],
    'Deaths With No Preexisting Condition' : vals[1],
    'Deaths Preexisting Condition Unknown' : vals[2],
  }

  return data


def getRecoveryData(local):
  print('Reovery Data')
  fileName = fileNames.recoveryScreenshot
  img = cv2.imread(fileName)
  crop_img = img[2000:-200, 100:-100]
  text = pytesseract.image_to_string(crop_img)
  textList = sanitizeText(text)
  print(textList)

  if local:
    cv2.imwrite('Recovery_totals.png', crop_img)

  vals = textList[1].split()

  data = {
    'Recovered With Preexisting Condition' : vals[0],
    'Recovered With No Preexisting Condition' : vals[1],
    'Recovered Preexisting Condition Unknown' : vals[2],
  }

  return data


def getLTCData(local):
  print('LTC Data')
  fileName = fileNames.ltcScreenshot
  img = cv2.imread(fileName)
  crop_img = img[150:-20, 100:-100]
  text = pytesseract.image_to_string(crop_img)
  textList = sanitizeText(text)
  print(textList)

  if local:
    cv2.imwrite('LTC_totals.png', crop_img)

  vals = textList[1].split()

  data = {
    'Current LTC Outbreaks' : vals[0],
    'LTC Positives' : vals[1],
    'LTC Recovered' : vals[2],
    'LTC Deaths' : vals[3],
  }

  return data

if __name__ == "__main__":
  local = 'DRONE_SYSTEM_HOST' not in os.environ


  if commitChecker.stillNeedTodaysData():
    data = {}

    try:
        data.update(getSummaryData(local))
    except:
        print('issue getting summary')
    try:
        data.update(getSerologyData(local))
    except:
        print('issue getting serology')
    try:
        data.update(getRMCCData(local))
    except:
        print('issue getting rmcc')
    try:
        data.update(getDeathData(local))
    except:
        print('issue getting deaths')
    try:
        data.update(getRecoveryData(local))
    except:
        print('issue getting recovery')
    try:
        data.update(getLTCData(local))
    except:
        print('issue getting LTC')

    try:
        data.update(getCaseData(local))
    except:
        print('issue getting cases')



    writeJson(fileNames.dailyJson, data)


    list_of_pdfs = glob.glob(os.path.join(fileNames.storageDir, '*.pdf'))
    pdfFile = max(list_of_pdfs, key=os.path.getctime)

    hospitalData = None
    try:
      hospitalData = readPDF(pdfFile)
      print(hospitalData)
    except:
      print('no hospital data')

    if not local:
      list_of_files = glob.glob(os.path.join(fileNames.storageDir, '*.csv'))
      csvFile = max(list_of_files, key=os.path.getctime)

      createGeoJson(csvFile, hospitalData)

    print(data)

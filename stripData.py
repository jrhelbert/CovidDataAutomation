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
  doc = PDFDocument(fd)
  all_pages = [p for p in doc.pages()]
  page_count = len(all_pages)
  viewer = SimplePDFViewer(fd)
  viewer.render()
  countyHospitalData = {}
  compiled = ""
 
  for i in range(page_count):
    pageText = "".join(viewer.canvas.strings)
    if 'Kossuth' not in pageText:
      try:
        viewer.next()
        viewer.render()
      except:
        print('end of doc and no county data')
    else:
      print('found county data')
      break

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


def convertVals(vals):
  newVals = []
  for val in vals:
    newVal = val
    if 'K' in val:
      newVal = int(float(val[:-1])*1000)
    newVals.append(newVal)
  return newVals


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

  vals = convertVals(vals)

  vents = vals[11]
  if vents == 7715:
    vents = 775
  data = {
    'Currently Hospitalized' : vals[1],
    'In ICU' : vals[3],
    'Newly Admitted' : vals[5],
    'Beds Available' : vals[7],
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

  vals = convertVals(textList[1].split())

  data = {
    'Individual Serologic Tests' : vals[0],
    'Individual Serologic Negatives' : vals[1],
    'Individual Serologic Positives' : vals[2],
  }

  return data


def getCaseData(local):
  print('Case Data')
  fileName = fileNames.caseScreenshot
  img = cv2.imread(fileName)
  crop_img = img[100:-80, 100:-100]

  textList = []
  pcrImg = crop_img[100:420, 10:-10]
  text = pytesseract.image_to_string(pcrImg)
  totalPCR = crop_img[100:420, 10:500]
  text = pytesseract.image_to_string(totalPCR)
  sanitizedText = sanitizeText(text)
  textList.append(sanitizedText[1])
  textList.append(sanitizedText[3])
  positivePCR = crop_img[100:420, 600:1100]
  text = pytesseract.image_to_string(positivePCR)
  sanitizedText = sanitizeText(text)
  textList.append(sanitizedText[1])
  textList.append(sanitizedText[3])
  negativePCR = crop_img[100:420, 1200:1700]
  text = pytesseract.image_to_string(negativePCR)
  sanitizedText = sanitizeText(text)
  textList.append(sanitizedText[1])
  textList.append(sanitizedText[3])

  pcrText = []
  for text in textList:
    pcrText.append(text.replace(' ', ''))
  pcrText = convertVals(pcrText)
  print(pcrText)
  
  textList = []
  antigenImg = crop_img[550:900, 10:-10]
  text = pytesseract.image_to_string(antigenImg)
  totalAntigen = crop_img[550:900, 10:500]
  text = pytesseract.image_to_string(totalAntigen)
  sanitizedText = sanitizeText(text)
  textList.append(sanitizedText[1])
  textList.append(sanitizedText[3])
  positiveAntigen = crop_img[550:900, 600:1100]
  text = pytesseract.image_to_string(positiveAntigen)
  sanitizedText = sanitizeText(text)
  textList.append(sanitizedText[1])
  textList.append(sanitizedText[3])
  negativeAntigen = crop_img[550:900, 1200:1700]
  text = pytesseract.image_to_string(negativeAntigen)
  sanitizedText = sanitizeText(text)
  textList.append(sanitizedText[1])
  textList.append(sanitizedText[3])

  antigenText = []
  for text in textList:
    antigenText.append(text.replace(' ', ''))
  antigenText = convertVals(antigenText)
  print(antigenText)

  totalsText = []
  textList = []
  totalsImg = crop_img[1000:1150, 10:-500]
  text = pytesseract.image_to_string(totalsImg)
  textList.extend(sanitizeText(text))
  totalsText.extend(textList[1].split())
  totalsText = convertVals(totalsText)
  print(totalsText)

  individualsText = []
  textList = []
  individualsImg = crop_img[1450:1600, 10:-500]
  text = pytesseract.image_to_string(individualsImg)
  textList.extend(sanitizeText(text))
  individualsText.extend(textList[1].split())
  individualsText = convertVals(individualsText)
  print(individualsText)

  breakDownText = []
  textList = []
  breakDownImg = crop_img[-200:-10, 10:-10]
  text = pytesseract.image_to_string(breakDownImg)
  textList.extend(sanitizeText(text))
  breakDownText.extend(textList[1].split())
  breakDownText = convertVals(breakDownText)
  print(breakDownText)


  if local:
    cv2.imwrite('Cases_pcr.png', pcrImg)
    cv2.imwrite('Cases_antigen.png', antigenImg)
    cv2.imwrite('Cases_totals.png', totalsImg)
    cv2.imwrite('Cases_individuals.png', individualsImg)
    cv2.imwrite('Cases_breakdown.png', breakDownImg)


  data = {
    'Total PCR Tests' : pcrText[0],
    'Individual PCR Tests' : pcrText[1],
    'Total PCR Negatives' : pcrText[2],
    'Individual PCR Negatives' : pcrText[3],
    'Total PCR Positives' : pcrText[4],    
    'Individual PCR Positives' : pcrText[5],
    'Total Antigen Tests' : antigenText[0],
    'Individual Antigen Tests' : antigenText[1],
    'Total Antigen Negatives' : antigenText[2],
    'Individual Antigen Negatives' : antigenText[3],
    'Total Antigen Positives' : antigenText[4],
    'Individual Antigen Positives' : antigenText[5],
    'Total Tests' : totalsText[0],
    'Total Negative' : totalsText[1],
    'Total Positive' : totalsText[2],
    'Total Individual Tests' : individualsText[0],
    'Total Individuals Negative' : individualsText[1],
    'Total Individuals Positive' : individualsText[2],
    'Cases With Preexisting Condition' : breakDownText[0],
    'Cases With No Preexisting Condition' : breakDownText[1],
    'Cases Preexisting Condition Unknown' : breakDownText[2],
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

  vals = convertVals(textList[1].split())

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

  vals = convertVals(textList[1].split())

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

  vals = convertVals(textList[1].split())

  data = {
    'Current LTC Outbreaks' : vals[0],
    'LTC Positives' : vals[1],
    'LTC Recovered' : vals[2],
    'LTC Deaths' : vals[3],
  }

  return data


def loadAllData():
  data = {}
  local = False

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

  return data


def readHospitalData():
  list_of_pdfs = glob.glob(os.path.join(fileNames.storageDir, '*.pdf'))
  list_of_pdfs.sort()
  pdfFile = list_of_pdfs[-1]

  hospitalData = None
  try:
    hospitalData = readPDF(pdfFile)
    print(hospitalData)
  except:
    print('no hospital data')
  return hospitalData


if __name__ == "__main__":

  if commitChecker.stillNeedTodaysData():
    data = loadAllData()
    writeJson(fileNames.dailyJson, data)

    hospitalData = readHospitalData()

    list_of_files = glob.glob(os.path.join(fileNames.storageDir, '*.csv'))
    list_of_files.sort()
    csvFile = list_of_files[-1]

    createGeoJson(csvFile, hospitalData)

    print(data)

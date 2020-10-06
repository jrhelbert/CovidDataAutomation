import time
import os
from seleniumUtils import *
import requests
import fileNames
import urls


def getHospitalData(local=False):
    filePath = None

    browser = getBrowser(urls.mainPage, height=1700, zoom=90)
    time.sleep(20)
    link = browser.find_element_by_link_text('Iowa Hospitalizations by County')
    html = link.get_attribute('outerHTML')
    htmlList = html.split('"')
    linkURL = htmlList[1]
    print(linkURL)

    if 'drive.google' in linkURL:
      linkURL = linkURL.replace('https://drive.google.com/file/d/', '')
      fileID = linkURL.replace('/view?usp=sharing', '')

      linkURL = 'https://drive.google.com/uc?export=download&id={}'.format(fileID)
    
    browser.get(linkURL)
    time.sleep(40)

    timeString = time.strftime("%Y-%m-%d %H%M")
    localFilePath = fileNames.countyHospitalFormat.format(timeString)
    if saveDownloadFile(browser, fileNames.storageDir, localFilePath):
      filePath = localFilePath
    closeBrowser(browser)

    return filePath


def getSummary(local=False):
    browser = getBrowser(urls.summaryPage, height=1700, zoom=90)
    time.sleep(20)
    saveScreenshot(browser, fileNames.summaryScreenshot)

    
    elements = browser.find_elements_by_class_name('cd-control-menu_container_2gtJe')
    button = elements[-2].find_element_by_css_selector("button[class='db-button small button cd-control-menu_option_wH8G6 cd-control-menu_expand_VcWkC cd-control-menu_button_2VfJA cd-control-menu_db-button_2UMcr ng-scope']")
    print('Clicking Download Button')
    browser.execute_script("$(arguments[0].click());", button)
    time.sleep(20)

    timeString = time.strftime("%Y-%m-%d %H%M")
    localPath = fileNames.storageSummaryFormat.format(timeString)
    saveDownloadFile(browser, fileNames.storageDir, localPath)

    if local:
      os.remove(localPath)

    closeBrowser(browser)


def getAccessVals():
  browser = getBrowser(urls.accessPage)
  
  titles = browser.find_elements_by_class_name('ss-title')
  elements = browser.find_elements_by_class_name('ss-value')

  vals = {}
  for i in range(len(titles)):
    vals[titles[i].get_attribute('innerHTML')] = elements[i].get_attribute('innerHTML')
  closeBrowser(browser)
  return vals


def getGeoJSON():
  r = requests.get(urls.dailyGeoJson, stream=True)
  if r.status_code == 200:
    filePath = fileNames.originalGeoJson
    if os.path.exists(filePath):
      os.remove(filePath)
    open(filePath, 'wb').write(r.content)
  return filePath


def getOriginalMap():
  browser = getBrowser(urls.argisMap)
  saveScreenshot(browser, fileNames.mapScreenshot)
  closeBrowser(browser)


def getCases():
  browser = getBrowser(urls.casePage, height=5000, zoom=90)
  time.sleep(20)
  saveScreenshot(browser, fileNames.caseScreenshot)
  closeBrowser(browser)


def getRecovery():
  browser = getBrowser(urls.recoveredPage, height=2500)
  time.sleep(20)
  saveScreenshot(browser, fileNames.recoveryScreenshot)
  closeBrowser(browser)


def getDeaths():
  browser = getBrowser(urls.deathsPage, height=2500)
  time.sleep(20)
  saveScreenshot(browser, fileNames.deathsScreenshot)
  closeBrowser(browser)


def getLTC():
  browser = getBrowser(urls.ltcPage, height=400)
  time.sleep(20)
  saveScreenshot(browser, fileNames.ltcScreenshot)
  closeBrowser(browser)


def getRMCCData():
  browser = getBrowser(urls.rmccPage, height=3300)
  saveScreenshot(browser, fileNames.rmccScreenshot)
  closeBrowser(browser)


def getSerologyData():
  browser = getBrowser(urls.serologyPage, zoom=80, height=400)
  saveScreenshot(browser, fileNames.serologyScreenshot)
  closeBrowser(browser)

local = 'DRONE_SYSTEM_HOST' not in os.environ

if not local:
  time.sleep(30)
  getGeoJSON()
  # print(getAccessVals())
  
getSummary(local)
getCases()
getRecovery()
getDeaths()
getLTC()
getOriginalMap()
getRMCCData()
getSerologyData()
getHospitalData()

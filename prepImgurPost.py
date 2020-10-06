import time
from seleniumUtils import *
import urls

def getMyMaps():
  browser = getBrowser(urls.detailedMaps)

  layerControl = browser.find_element_by_class_name('leaflet-control-layers-base')
  labels = layerControl.find_elements_by_xpath(".//span")
  buttons = layerControl.find_elements_by_class_name("leaflet-control-layers-selector")
  for i in range(len(labels)):
    labelList = labels[i].get_attribute('innerHTML').split()
    label = "{}{}.png".format(labelList[1], labelList[0]).lower()
    browser.execute_script("$(arguments[0].click());", buttons[i])
    time.sleep(10)
    saveScreenshot(browser, label)

  closeBrowser(browser)

try:
  getMyMaps()
except:
  print('unable to get my map screenshots')

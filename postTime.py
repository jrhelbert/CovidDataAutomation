import time

def shouldPost():
  post = False
  current_time = time.strftime("%H:%M:%S")
  start = '15:00:00'
  end = '17:00:00'
  if current_time > start and current_time < end:
    post = True
  else:
    print('Not in posting timeframe skipping post')
    print(current_time)
  return post
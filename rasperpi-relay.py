import settings
import time
import json
from urllib.request import urlopen
from urllib.parse import urlencode
from pyRF24 import pyRF24

radio = pyRF24("/dev/spidev0.0", 8000000, 25, retries = (15, 15), channel = settings.channel, dynamicPayloads = True, autoAck = True, ackPayload = True)
radio.openWritingPipe(settings.writing_pipe)
radio.openReadingPipe(1, settings.reading_pipe)
radio.printDetails()

radio.startListening()
while True:
  while radio.available():
    # read events from arduino
    len = radio.getDynamicPayloadSize()
    payload = radio.read(len)[:len].split()
    print("Received: ", payload)
    if payload[0] not in (b'COOLED', b'COOL', b'BURN', b'BURNED'): continue

    # send events to server, and receive any commands returned
    data = urlencode({'event': payload[0].lower(), 'timestamp': payload[1]}).encode("utf-8")
    cmds = []
    try:
      result = urlopen(settings.server_event_url, data).read().decode('utf-8')
      cmds = json.loads(result)
      print("Commands: ", cmds)
    except Exception as err:
      print("Report to server failed: ", err)

    # send commands to arduino
    if isinstance(cmds, list):
      for cmd in cmds:
        command = (cmd['command'] + cmd['argument']).encode('utf-8')
        radio.writeAckPayload(1, command)

  time.sleep(0.01)


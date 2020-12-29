
address = "D7:E9:93:DD:9A:2F"
CHARACTERISTIC_UUID = "533e1541-3abe-f33f-cd00-594e8b0a8ea3"

import logging
import asyncio

from bleak import BleakClient
from bleak import _logger as logger

import uinput
import bitstruct

"""
Service UUID 0x1531, one characteristic that has read and notify, returns 20 byte more than 1/second (haven't determined actually rate).

    value[8]
    D-pad Up: 0x01
    D-pad Down: 0x02
    D-pad Left: 0x04
    D-pad Right: 0x08
    A Button: 0x10
    B Button: 0x20
    X Button: 0x40
    Y Button: 0x80
    value[9]
    L1: 0x10
    R1: 0x20
    value[10] L2 when 0xFF
    value[11] R2 when 0xFF
    value[12] Right stick x-axis as a signed byte
    value[13] Right stick y-axis as a signed byte
    value[14] Left stick x-axis as a signed byte
    value[15] Left stick y-axis as a signed byte
"""

fmt = bitstruct.compile('p64u1u1u1u1u1u1u1u1p2u1u1p1u1p2p7u1p7u1s8s8s8s8')
"""
    events = (
        uinput.BTN_JOYSTICK,
        uinput.ABS_X + (0, 255, 0, 0),
        uinput.ABS_Y + (0, 255, 0, 0),
        )

    with uinput.Device(events) as device:
        for i in range(20):
            # syn=False to emit an "atomic" (5, 5) event.
            device.emit(uinput.ABS_X, 5, syn=False)
            device.emit(uinput.ABS_Y, 5)
        device.emit_click(uinput.BTN_JOYSTICK)
"""
events = (
    uinput.BTN_Y,
    uinput.BTN_X,
    uinput.BTN_B,
    uinput.BTN_A,
    uinput.BTN_DPAD_RIGHT,
    uinput.BTN_DPAD_LEFT,
    uinput.BTN_DPAD_DOWN,
    uinput.BTN_DPAD_UP,
    uinput.BTN_TR,
    uinput.BTN_TL,
    uinput.BTN_START,
    uinput.BTN_THUMBL,
    uinput.BTN_THUMBR,
    uinput.ABS_RX,
    uinput.ABS_RY,
    uinput.ABS_X,
    uinput.ABS_Y,
)

NEVENTS = 17
prev = [None for x in range(NEVENTS)]

device = uinput.Device(events)
def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    # print("{0}: {1}".format(sender, data))
    global prev
    unpacked = fmt.unpack(data)
    diff = False
    for i in range(NEVENTS):
        val = unpacked[i]
        if val != prev[i]:
            diff = True
            ev = events[i]
            if ev[0] == 1: # KEY
                device.emit(ev, unpacked[i], syn=False)
            elif ev[0] == 3: # ABS
                device.emit(ev, unpacked[i], syn=False)
    if diff:
        device.syn()
        #print("%s" % str(unpacked))
    prev = unpacked

async def run(client, debug=False):
    if debug:
        import sys

        l = logging.getLogger("asyncio")
        l.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        l.addHandler(h)
        logger.addHandler(h)

    x = await client.connect()
    logger.info("Connected: {0}".format(x))

    await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
    while True:
        await asyncio.sleep(2.0)
        # dummy read to keep the connection alive
        v = await client.read_gatt_char(CHARACTERISTIC_UUID)
        #print("%s" % str(v))


if __name__ == "__main__":
    import os

    #os.environ["PYTHONASYNCIODEBUG"] = str(1)
    loop = asyncio.get_event_loop()
    #loop.set_debug(True)

    client = BleakClient(address)

    try:
        loop.run_until_complete(run(client, True))
    except KeyboardInterrupt:
        print("Received exit, exiting")
    except Exception as e:
        raise
    finally:
        print("disconnecting...")
        client.stop_notify(CHARACTERISTIC_UUID)
        client.disconnect()




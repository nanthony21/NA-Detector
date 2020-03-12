from instrumental import instrument, list_instruments

def setExposure(cam, exp):
    cam.stop_live_video()
    # time.sleep(.05)  # This delay helps prevent a hard crash. Still happens sometimes though.
    cam.start_live_video(exposure_time=f"{exp} ms")  # This is to update the exposure used.

if __name__ == '__main__':
    inst = list_instruments()
    cam = instrument(list_instruments()[0])  # Replace with your camera's alias
    cam.start_live_video(exposure_time=f"{10} ms")
    for i in range(10, 1000):
        setExposure(cam, i)

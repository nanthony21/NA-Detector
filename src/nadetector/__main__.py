from instrumental import instrument, list_instruments
from nadetector.hardware import TestCamera
from nadetector.app import App
import sys
import os
from nadetector._resources import driverPath


def main():
    os.environ['PATH'] += ';' + str(driverPath)  # This makes is so that the Camera driver DLL can be found.

    test: bool = False  # If true then use a simulated camera.

    def tracefunc(frame, event, arg, indent=[0]):
        if event == "call":
            indent[0] += 2
            print("-" * indent[0] + "> call function", frame.f_code.co_name)
        elif event == "return":
            print("<" + "-" * indent[0], "exit function", frame.f_code.co_name)
            indent[0] -= 2
        return tracefunc

    cam = None
    if test:
        cam = TestCamera((512, 1024), 10, ring=True)
    else:
        inst = list_instruments()
        print(f"Found {len(inst)} cameras:")
        print(inst)
        if len(inst) > 0:
            cam = instrument(list_instruments()[0])  # Replace with your camera's alias

    if cam is not None:
        with cam:
            app = App(sys.argv, cam)
            # Initial settings for the app
            app.window.videoButton.click()  # Start the video
            app.window.advancedDlg.cameraTab.autoExposeCB.click()  # Turn on autoexposure
            # sys.setprofile(tracefunc)
            app.exec_()


if __name__ == '__main__':
    main()

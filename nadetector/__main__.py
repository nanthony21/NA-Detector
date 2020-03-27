from instrumental import instrument, list_instruments
from nadetector.hardware.testCamera import TestCamera
from nadetector.camera_gui import App
import sys


def main():
    test = False

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

            app.exec_()


if __name__ == '__main__':
    main()

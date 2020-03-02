# -*- coding: utf-8 -*-
# Copyright 2015-2017 Nate Bogdanowicz
"""
A very simple GUI that uses a CameraView to view live video from a camera.
"""
import sys
from qtpy.QtWidgets import (QApplication, QMainWindow, QWidget, QScrollArea, QPushButton,
                            QVBoxLayout, QHBoxLayout)
from instrumental import instrument, gui, list_instruments

import os

os.environ['PATH'] += os.path.abspath('lib')

class App(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.aboutToQuit.connect(self.about2Quit)
        
        self.camview = gui.CameraView(cam)
        self.window = Window(self.camview)
        
        
        self.window.show()
        
    def about2Quit(self):
        if window.button.running:
            self.camview.stop_video()
        
class Window(QMainWindow):
    def __init__(self, camview: gui.CameraView):
        super().__init__()
        
        main_area = QWidget()
        button_area = QWidget()
        self.scroll_area = QScrollArea()
        self.button = QPushButton("Start Video")
        self.btn_grab = QPushButton("Grab Frame")
        
        self.scroll_area.setWidget(camview)
        
        self.button.running=False
        def start_stop():
            if not self.button.running:
                camview.start_video()
                self.button.setText("Stop Video")
                self.button.running = True
            else:
                camview.stop_video()
                self.button.setText("Start Video")
                self.button.running = False
        self.button.clicked.connect(start_stop)
        
        def grab():
            if not self.button.running:
                camview.grab_image()
        self.btn_grab.clicked.connect(grab)
    
        # Create layouts
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
    
        # Fill Layouts
        vbox.addWidget(self.scroll_area)
        vbox.addWidget(button_area)
        hbox.addStretch()
        hbox.addWidget(self.button)
        hbox.addWidget(self.btn_grab)
    
        # Assign layouts to widgets
        main_area.setLayout(vbox)
        button_area.setLayout(hbox)
        self.scroll_area.setLayout(QVBoxLayout())
    
        # Attach some child widgets directly
        self.setCentralWidget(main_area)



if __name__ == '__main__':
    cam = instrument(list_instruments()[0])  # Replace with your camera's alias

    with cam:
        app = App(sys.argv)
        app.exec_()
        

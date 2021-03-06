from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QWIDGETSIZE_MAX


class AspectRatioWidget(QWidget):
    def __init__(self, aspect: float, parent: QWidget = None):
        super().__init__(parent)
        self._aspect = aspect

    def resizeEvent(self, event: QtGui.QResizeEvent):
        w, h = event.size().width(), event.size().height()
        self._resize(w, h)

    def _resize(self, width, height):
        newHeight = width / self._aspect #The ideal height based on the new commanded width
        newWidth = height * self._aspect #the ideal width based on the new commanded height
        #Now determine which of the new dimensions to use.
        if width > newWidth:
            self.setMaximumWidth(newWidth)
            self.setMaximumHeight(QWIDGETSIZE_MAX)
        else:
            self.setMaximumHeight(newHeight)
            self.setMaximumWidth(QWIDGETSIZE_MAX)

    def setAspect(self, aspect: float):
        self._aspect = aspect
        self._resize(self.width(), self.height())
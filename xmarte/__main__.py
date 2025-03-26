'''
Main entry point to the application from the module instance in site-packages
'''

import os

from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtCore import Qt

from xmarte import qt

qt.splash = None

if __name__ == "__main__":
    app = QApplication([])
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    pixmap_file = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "splashscreen.jpg")
    )
    pixmap = QPixmap(pixmap_file)
    screen_resolution = QApplication.instance().desktop().screenGeometry().size()
    SIZE_RATIO = 0.5
    scaled_width = int(screen_resolution.width() * SIZE_RATIO)
    scaled_height = int(screen_resolution.height() * SIZE_RATIO)
    scaled_image = pixmap.scaled(scaled_width, scaled_height,
                                    aspectRatioMode=Qt.KeepAspectRatio)

    qt.splash = QSplashScreen(scaled_image)
    qt.splash.show()
    qt.splash.setStyleSheet("font-size: 15px; font-weight: bold;")

    qt.splash.showMessage("<h1><font color='white'>Importing modules...</font></h1>",
        Qt.AlignBottom | Qt.AlignLeft, QColor("white"))

    win = qt.XMARTeTool(app)
    win.show()
    app.exec_()

''' The chart instance used in graph window for plotting '''
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChartView

def defineAxis(axis):
    '''Defines the axis based on the orientation.'''
    if axis.orientation() == Qt.Horizontal:
        axis.setTitleText("Time (s)")

    axis.show()


class PlotChart(QChartView):
    '''A plot chart.'''
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.viewport().installEventFilter(self)
        self.setContentsMargins(0,0,0,0)

    def eventFilter(self, obj, event):
        '''Catch potential events in chart.'''
        return super().eventFilter(obj, event)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        '''All user to control time axis change.'''
        if event.button() == 2:
            chart = self.chart()
            for axis in chart.axes():
                if axis.orientation() == Qt.Horizontal:
                    axis.setRange(
                        min(a.x() for a in chart.series()[0].pointsVector()),
                        max(a.x() for a in chart.series()[0].pointsVector()),
                    )
                defineAxis(axis)
            return None
        return super().mouseReleaseEvent(event)

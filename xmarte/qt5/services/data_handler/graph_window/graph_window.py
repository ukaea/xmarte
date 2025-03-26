''' The main window instance for the graph viewing tool of node data '''

import os

from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from PyQt5.QtCore import Qt
from PyQt5.QtChart import QChart, QChartView
from PyQt5.QtWidgets import (QMainWindow,
                             QWidget,
                             QMenuBar,
                             QMenu,
                             QAction,
                             QFileDialog,
                             QHBoxLayout,
                             QVBoxLayout,
                             QSizePolicy,
                             QSplitter)

from xmarte.qt5.services.data_handler.graph_window.plot.plot_node import PlotNode
from xmarte.qt5.services.data_handler.graph_window.plot.plot_chart import PlotChart
from xmarte.qt5.services.data_handler.graph_window.node_picker import NodePicker
from xmarte.qt5.services.data_handler.graph_window.graph.graph_scene import GraphEditorWidget
from xmarte.qt5.libraries.functions import deepcopyWithoutAttribute, updateDefaultDialogDir


class GraphWindow(QMainWindow):
    '''Create a new graph window and copy in each state scene.'''
    def __init__(self, application, parent_plugin):
        super().__init__()
        self.setWindowTitle("Graph View")
        self.application = application
        self.parent_plugin = parent_plugin
        self.application.newwindow = self
        self.scenes = deepcopyWithoutAttribute(self.application.state_scenes, 'application')
        self.screen = self.application.app.primaryScreen()
        self.size = self.screen.size()
        self.setGeometry(
            int(self.size.width() * 0.15),
            int(self.size.height() * 0.15),
            int(self.size.width() * 0.7),
            int(self.size.height() * 0.7),
        )
        self.setCentralWidget(QWidget(self))
        self._createMenuBar()
        self.redraw()
        self.show()

    def _createMenuBar(self):
        ''' Create the windows menu bar '''
        menuBar = QMenuBar(self)
        fileMenu = QMenu("&File", self)

        exitAction = QAction("&Exit", self)
        exportAction = QAction("&Export as PDF", self)
        saveAction = QAction("&Save", self)
        loadAction = QAction("&Load", self)
        exportAction.triggered.connect(self.export)
        exitAction.triggered.connect(self.exit)
        saveAction.triggered.connect(self.save)
        loadAction.triggered.connect(self.load)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(loadAction)
        fileMenu.addAction(exportAction)
        fileMenu.addAction(exitAction)
        menuBar.addMenu(fileMenu)
        self.setMenuBar(menuBar)

    def export(self):
        ''' Export our data set to file '''
        filename = QFileDialog.getSaveFileName(self, "Save Diagram", "", "pdf (*.pdf)")
        if filename[0]:
            if not (filename := filename[0]).endswith('.pdf'):
                filename += '.pdf'
            # Create a PdfPages object to save the plots
            with PdfPages(filename) as pdf:
                # Create and save multiple plots
                for i in self.rightlayout.history:  # Create 5 plots for demonstration
                    # Create some sample data for each plot
                    plt.figure(figsize=(6, 4))
                    for serial in i.chart().series():
                        x = [a.x() for a in serial.pointsVector()]
                        y = [a.y() for a in serial.pointsVector()]
                        plt.plot(x, y)

                    plt.xlabel('X-axis')
                    plt.ylabel('Y-axis')
                    plt.title(i.chart().title())  # Add title for each plot

                    # Save the plot to the PDF
                    pdf.savefig()

                    # Close the plot to release memory (optional)
                    plt.close()

    def exit(self):
        ''' Close Window '''
        self.close()

    def save(self):
        ''' Save our scene plots to file '''
        default_dir = ""
        if "file_location" in self.application.settings["GeneralPanel"].keys():
            default_dir = self.application.settings["GeneralPanel"]["file_location"]

        # Save the data setup to file
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Graph View", default_dir, "graph report (*.xgraph);;"
        )
        if filename:
            if not filename.endswith('.xgraph'):
                filename += '.xgraph'
            self.editor.scene.saveToFile(filename)
            self.application.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)
            updateDefaultDialogDir(os.path.dirname(filename))

    def load(self): # pylint: disable=R0912
        ''' Load a scene plot from file '''
        default_dir = ""
        if "file_location" in self.application.settings["GeneralPanel"].keys():
            default_dir = self.application.settings["GeneralPanel"]["file_location"]
        # Load data setup from file
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Graph Report", default_dir, "graph report (*.xgraph)"
        )
        if filename: # pylint: disable=R1702
            for node in self.editor.scene.nodes:
                if isinstance(node, PlotNode):
                    node.remove(admin=True)
                else:
                    node.remove()
            self.editor.scene.loadFromFile(filename)
            self.application.settings["GeneralPanel"]["file_location"] = os.path.dirname(filename)

            plotnode = None
            for node in self.editor.scene.nodes:
                # For each node, try to find it's associated node in the other scene.
                if isinstance(node, PlotNode):
                    plotnode = node
                    continue
                node.content.updateDim()
                # Find our node in our scenes:
                for _, state in self.application.state_scenes.items():
                    for _, thread in state.items():
                        for function in thread.nodes:
                            if function.title == node.title:
                                # Found our node, set the data up
                                for output_1, output_2 in zip(node.outputs, function.outputs):
                                    output_1.data = output_2.data

            for chart_view in self.rightlayout.history:
                chart_view.setParent(None)
                chart_view.deleteLater()

            if plotnode:
                plotnode.application = self.editor.scene.application
                plotnode.chart_list = []
                plotnode.charts = self.rightlayout
                plotnode.charts.history = []
                plotnode.chart_view = self.editor.scene.application.rightpanel # pylint:disable=E1101
                plotnode.grNode.contextMenuEvent = plotnode.replacemenu
                for input_socket in list(reversed(plotnode.inputs)):
                    if input_socket.label == '...':
                        continue
                    plotnode.onInputChanged(input_socket)

            else:
                # Recreate plot node
                node = PlotNode(self.editor.scene, "plots", [(0, "..."), (0, "Plot 1")], [])
                node.chart_list = []
                node.charts = self.rightlayout

                self.editor.scene.addNode(node)
            updateDefaultDialogDir(os.path.dirname(filename))

    def redraw(self):
        '''Create a left panel to display the nodes and scene and a
        right panel to display the graph.'''
        layout = QHBoxLayout()
        self.widget = QWidget(self)
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)
        self.splitter.setStretchFactor(1, 1)

        # On the left is the selection panel and nodeeditor view
        self.leftpanel = QWidget(self)
        leftlayout = QVBoxLayout()
        self.leftpanel.setLayout(leftlayout)
        self.splitter.addWidget(self.leftpanel)

        self.editor = GraphEditorWidget(self)
        self.editor.scene.application = self
        self.editor.scene.application.plugins = self.application.plugins
        self.editor.scene.owner = self
        self.editor.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Add our dark chart to the right hand panel
        self.rightpanel = QWidget(self)
        self.rightlayout = QSplitter(Qt.Vertical)
        rightlayout = QVBoxLayout()
        self.rightpanel.setLayout(rightlayout)
        rightlayout.addWidget(self.rightlayout)

        # Populate Selection Panel
        self.selectionpanel = NodePicker(self, self.application, self.editor, self)
        self.selectionpanel.rightlayout = self.rightlayout
        leftlayout.addWidget(self.selectionpanel)

        # Give our node it's plot node
        leftlayout.addWidget(self.editor)
        self.show()
        node = PlotNode(self.editor.scene, "plots", [(0, "..."), (0, "Plot 1")], [])
        node.chart_list = []
        node.charts = self.rightlayout

        self.nodeview = node

        self.editor.scene.grScene.setFocusItem(node.grNode)

        # Line Chart
        chart_view = PlotChart(QChart())
        self.rightlayout.history = [chart_view]
        self.rightlayout.plotnode = node
        self.rightlayout.setContentsMargins(0,0,0,0)
        chart_view.setRubberBand(QChartView.HorizontalRubberBand)
        chart_view.setContextMenuPolicy(Qt.CustomContextMenu)
        chart_view.chart().setTitle("Plot 1")
        chart_view.chart().setTheme(QChart.ChartThemeDark)
        self.rightlayout.addWidget(chart_view)
        node.chart_list += [chart_view.chart()]
        self.splitter.addWidget(self.rightpanel)
        self.splitter.setSizes([1, 1])

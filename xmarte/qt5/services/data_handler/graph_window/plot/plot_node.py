''' The plot node which is used to define plot graphs '''
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtChart import QChart, QChartView, QLineSeries

from xmarte.qt5.nodes.node_graphics import NodeContent
from xmarte.qt5.services.data_handler.graph_window.plot.plot_chart import PlotChart
from xmarte.qt5.services.data_handler.graph_window.graph.graph_node import GraphNode
from xmarte.qt5.services.data_handler.graph_window.plot.plot_socket import PlotSocket
from xmarte.qt5.services.data_handler.graph_window.plot.plot_graphics_node import PlotGraphicsNode


class PlotNode(GraphNode):
    '''Node which controls what is plotted on the graph in the right panel.'''
    Socket_class = PlotSocket
    GraphicsNode_class = PlotGraphicsNode
    NodeContent_class = NodeContent
    graph = False

    def __init__(
        self,
        scene=None,
        title: str = "Undefined Node",
        inputs: list = [],
        outputs: list = [],
    ):
        self.application = scene.application
        self.chart_list = []
        self.charts = None
        super().__init__(scene=scene, title=title, inputs=inputs, outputs=outputs)
        self.chart_view = scene.application.rightpanel
        self.grNode.contextMenuEvent = self.replacemenu

    def replacemenu(self, s):
        '''
        Replace node context menus with empty function
        '''

    def remove(self, admin=False):
        '''Override remove method. User should not delete the plot node.'''
        if admin:
            super().remove()
            self.scene.removeNode(self, admin=True)
            del self

    def onInputChanged(self, socket: "Socket"): # pylint:disable=R0914,R0912,R0915
        '''
        Handler for when a new input is connected to the plot node socket
        '''
        # Okay so now we want to figure out which socket number - then get it's corresponding chart
        # Then we get the input data node and grab it's data
        def createChart(self):
            chart_view = PlotChart(QChart())
            chart_view.chart().setTitle(socket.label)
            chart_view.setRubberBand(QChartView.HorizontalRubberBand)
            chart_view.setContextMenuPolicy(Qt.CustomContextMenu)
            chart_view.chart().setTheme(QChart.ChartThemeDark)
            self.chart_list += [chart_view.chart()]
            self.charts.addWidget(chart_view)
            self.charts.history += [chart_view]

        if len(socket.edges) > 0:
            if socket.label == "...":
                # Rename socket
                socket.label = "Plot " + str(len(self.inputs))
                # Create new Socket
                chartno = len(self.inputs) - 1
                # Add Chart to our chart view
                createChart(self)
                socket.index = len(self.inputs)
            else:
                chartno = None
                for i, chartview in enumerate(self.charts.history):
                    if chartview.chart().title() == socket.label:
                        chartno = i
                        break
                if chartno is None:
                    # Create the chart again
                    createChart(self)
                    chartno = len(self.charts.history) - 1
            # Get our chart
            chart = self.chart_list[chartno]
            # Okay so now we have a chartno we need to wipe our chart and write the data from
            # all sources to it
            chart.removeAllSeries()

            for edge in socket.edges:
                data = edge.start_socket.data
                label = edge.start_socket.label
                if data is not None:
                    series = QLineSeries()
                    series.setName(label)
                    for x, y in enumerate(data):
                        series.append(QPointF(float(x), float(y)))
                    chart.addSeries(series)

            # # Here we need logic to work out our axis
            chart.createDefaultAxes()
        else:
            # Remove the chart and the socket
            # Do not remove socket if socket.label = Plot 1 and no other sockets available
            if len(self.inputs) > 2 and not socket.label == "...":
                self.inputs = [a for a in self.inputs if a is not socket]

                for chart in self.chart_list:
                    if chart.title() == socket.label:
                        chart.setParent(None)
                        chart.deleteLater()
                for chart_view in self.charts.history:
                    if chart_view.chart().title() == socket.label:
                        chart_view.setParent(None)
                        chart_view.deleteLater()
                self.chart_list = [
                    a for a in self.chart_list if not (a.title() == socket.label)
                ]
                self.charts.history = [
                    a
                    for a in self.charts.history
                    if not (a.chart().title() == socket.label)
                ]
                socket.delete()
                # Ensure everythings named correctly
                for idx, input_socket in enumerate(self.inputs):
                    input_socket.label = "Plot " + str(idx + 1)
                    input_socket.index = idx + 1
                count = 1
                for chart_view in self.chart_view.children():
                    if isinstance(chart_view, PlotChart):
                        chart_view.chart().setTitle("Plot " + str(count))
                        count = count + 1
                self.inputs[-1].label = "..."
        # reorder sockets to plot names
        if not any(x.label == "..." for x in self.inputs):
            self.inputs += [
                PlotSocket(
                    self,
                    len(self.inputs),
                    socket_type=0,
                    label="...",
                    is_input=True,
                    position=self.input_socket_position,
                )
            ]
        for inputs in self.inputs:
            inputs.count_on_this_node_side = len(self.inputs)
            if "..." in inputs.label:
                inputs.index = 0
            else:
                inputs.index = len(self.inputs) - int(inputs.label.split(" ")[1])
        # Update all graphically
        self.updateSocketPositions()
        for inputs in self.inputs:
            for edge in inputs.edges:
                edge.updatePositions()
        self.updateHeight()

        if len(self.chart_list) > 0:
            layoutheight = int(self.scene.application.rightlayout.height()/len(self.chart_list))
            sizes = [layoutheight for a in self.chart_list]
            self.scene.application.rightlayout.setSizes(sizes)
        ## Evenly distribute the charts heights
        self.grNode.update()
        self.grNode.setContentDim()

    def updateHeight(self):
        '''
        Update the height
        '''
        minheight = 0
        for inputs in self.inputs:
            minheight = minheight + inputs.grSocket.boundingRect().height()
        if (minheight + self.grNode.title_height + 50) > (
            self.grNode.height - self.grNode.title_height
        ):
            self.grNode.height = (minheight + (self.grNode.title_height * 2)) + 50
        self.grNode.content.setFixedHeight(
            int((minheight + self.grNode.title_height) + 50)
        )

    def serialize(self):
        ''' Serialise '''
        res = super().serialize()
        res["type"] = "PlotNode"
        return res

    def deserialize(self, data, hashmap={}, restore_id=True, *args, **kwargs): # pylint:disable=W1113
        ''' Deserialise '''
        res = super().deserialize(data, hashmap, restore_id)
        return res

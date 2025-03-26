'''
A static library of functions that can be performed on application nodes
'''
import math
from typing import List
from operator import itemgetter
from martepy.marte2.datasource import MARTe2DataSource
from martepy.functions.extra_functions import getname

from xmarte.qt5.libraries.functions import fixSocketOrdering

from xmarte.qt5.widgets.scene import EditorScene

class ExecutionOrderGroup:
    """
    A data structure for the execution order. This should be extended
    with a subclass for whatever may want to use this application.
    """
    def __init__(self):
        ''' Basic initialisation of local variables group number and nodes list '''
        self.group_number = None
        self.nodes = []

class NodeHandler:
    """
    A static library manipulating the nodes within the scene in standard ways to get nodes
    in specific contexts.
    """
    @staticmethod
    def setItemPos(node, node_position):
        ''' First we find the node via the block '''
        node.setPos(node_position[0], node_position[1])

    @staticmethod
    def getNodes(scene, safe=False):
        """
        Return a virtual instance of the current nodes within the scene
        The safe parameter specifies whether we want to grab a read only
        copy of our scene (True) or False for where we want the scene itself
        to be modified by the unflattening process.
        """
        nodes = []
        # Handle duplicate nodes in scene
        if safe:
            # In order to do a deepcopy we can't have our application instance
            # linked anywhere here.
            # We do this to safely copy our scene first
            deserialised = scene.serialize()
            newscene = EditorScene(scene.application, real=False)
            hashmap = {}
            newscene.deserialize(deserialised, hashmap)
            scene = newscene
        for node in scene.nodes:
            if not any(x.id == node.id for x in nodes):
                nodes.append(node)
        return nodes

    @staticmethod
    def getRealNodes(input_nodes):
        """
        Based on a set of nodes we want to rule out duplicates or ones
        without a graphical instance of themselves (subnodes internal nodes
        still have a graphical instance, but this only skims the first layer.
        """
        nodes = []
        # Handle duplicate nodes in scene
        for node in input_nodes:
            if not any(x.id == node.id for x in nodes) and node.grNode is not None:
                nodes.append(node)
        return nodes

    @staticmethod
    def getLinkedBlocks(nodes):
        """
        For a list of nodes, return tuples which give the pairings of nodes of IO
        for each edge/connection, there is a tuple pair of the node to and node
        from
        """
        block_linked_pairs = []
        for node in nodes:
            # node.feed_output_blocks()
            # Generate block linked pairs
            for node_input in node.inputs:
                if len(node_input.edges) > 0:
                    block_from = node_input.edges[0].start_socket.node
                    block_to = node
                    block_linked_pairs.append((block_from, block_to))

        return block_linked_pairs

    @staticmethod
    def resolveInputs(nodes):
        '''
        This function works to set the input signals of nodes to whatever
        the output signal of the connected edge is.
        '''

        # First make sure our orderings match
        for node in nodes:
            fixSocketOrdering(node)

        # If the input is a datasource, make sure we set the DataSource field
        # Set the Alias to the input name
        for node in nodes:
            for input_socket, input_config in zip(node.inputs,node.inputsb):
               # Now we enforce rules based on what the GAM is (for now)
                if 'Default' in input_config[1]['MARTeConfig'].keys():
                    del input_config[1]['MARTeConfig']['Default']
                if node.btype == "IOGAM":
                    if len(input_socket.edges) > 0:
                        source = input_socket.edges[0].start_socket.node
                        if isinstance(node.application.API.toGAM(source), MARTe2DataSource):
                            input_config[1]['MARTeConfig']['DataSource'] = getname(source)
            for output_socket, output_config in zip(node.outputs, node.outputsb):
                if len(output_socket.edges) > 0:
                    source = output_socket.edges[0].end_socket.node
                    if isinstance(node.application.API.toGAM(source), MARTe2DataSource):
                        output_config[1]['MARTeConfig']['DataSource'] = getname(source)

    @staticmethod
    def recursiveRankInputsIfNotRank0(
        target_row_number,
        start_rank,
        _recurse_count,
        _rank_latest_row_number,
        ranks_by_row_number,
        chain={},
        node_tuples=[],
    ):
        """
        Recursively algorithm for ranking backwards a node
        """
        if target_row_number is None:
            target_row_number = 1
        chain[start_rank] = target_row_number
        _recurse_count += 1
        # if start_rank > 30: exit()

        if ranks_by_row_number[target_row_number] >= start_rank:
            # The rank is high enough that this block will happen before
            # the block that reads it already
            del chain[start_rank]
            return

        if any(
            (
                _rank_latest_row_number.get(i, None) == target_row_number
                for i in range(start_rank)
            )
        ):
            # If we come across this row number as the most recently written
            # row numbers in the lower (later) ranks, then we stop or we
            # run into circular reference failings.
            del chain[start_rank]
            return

        # Apply the new rank
        ranks_by_row_number[target_row_number] = start_rank
        _rank_latest_row_number[start_rank] = target_row_number

        # Now check if this row number contained a 'rank0' class, and if
        # not recursively rank the input signals to happen earlier than
        # this row
        node = NodeHandler.getNodeByIdx(node_tuples, target_row_number)
        if not node.rank and hasattr(node, "inputs"):
            for ninput in node.inputs:
                if len(ninput.edges) == 0:
                    continue

                input_idx = NodeHandler.getInputNodeIdx(ninput, node_tuples)
                if input_idx is None:
                    if target_row_number is None:
                        target_row_number = 1
                    input_idx = target_row_number
                NodeHandler.recursiveRankInputsIfNotRank0(
                    input_idx,
                    start_rank + 1,
                    _recurse_count,
                    _rank_latest_row_number,
                    ranks_by_row_number,
                    chain,
                    node_tuples,
                )
        del chain[start_rank]

    # This function is a replication from a old system - it should remain unchanged at all costs
    @staticmethod
    def getExecutionGroups(nodes, improved_algorithm=True) -> List[ExecutionOrderGroup]: # pylint: disable=R0914
        """
        This algorithm is a recursive methodology partially grabbed from the original
        rtcc1 code. Modifications are:
        - Move from usage of order number/line number to position in scene/diagram
        - Improved algorithm introduced later in rtcc1 also available as flag.
        
        Calculates and returns (but does not store) the execution order
        groups as would be applied if a given network were loaded by RTCC1.

        In that scheme, rank 0 means 'run me last' and is applied to blocks
        which output to real actuators. "isOrderingRank0" will return true
        for those which are outputing to these actuators, plus RTPS which is
        handled separately at the end.

        The RTPS blocks must run first in RTCC1 as they can alter the "time"
        value that all other blocks may use.

        There is a correction/improvement that can be applied to this algorithm
        which was probably intended to be in the original. For reproducing old
        pulses, we need the unimproved version, but for drawing networks out
        the improved version is preferred.
        """

        # First we want to give all nodes a random ranking
        node_tuples = []
        for idx, node in enumerate(nodes):
            node_tuples.append((node, idx + 1))

        ranks_by_row_number = {i: -1 for i in range(1, len(nodes) + 1)}

        _rank_latest_row_number = {}
        _recurse_count = 0
        # Now we need to use this in line with the previous algorithm solver
        reverse_order_nodes = list(reversed(sorted(node_tuples, key=itemgetter(1))))

        # Step 1 of the algorithm: apply rank 0 to the inputs of all 'rank0'
        # class blocks
        for node_tuple in reverse_order_nodes:
            node = node_tuple[0]
            node_index = node_tuple[1]

            if improved_algorithm:
                NodeHandler.recursiveRankInputsIfNotRank0(
                    node_index,
                    0,
                    _recurse_count,
                    _rank_latest_row_number,
                    ranks_by_row_number,
                    {},
                    node_tuples,
                )
                if hasattr(node, "inputs"):
                    for ninput in node.inputs:
                        if len(ninput.edges) == 0:
                            continue

                        input_idx = NodeHandler.getInputNodeIdx(ninput, node_tuples)
                        NodeHandler.recursiveRankInputsIfNotRank0(
                            input_idx,
                            1,
                            _recurse_count,
                            _rank_latest_row_number,
                            ranks_by_row_number,
                            {0: node_index},
                            node_tuples,
                        )
            else:
                if hasattr(node, "inputs"):
                    for ninput in node.inputs:
                        if len(ninput.edges) == 0:
                            continue

                        input_idx = NodeHandler.getInputNodeIdx(ninput, node_tuples)
                        NodeHandler.recursiveRankInputsIfNotRank0(
                            input_idx,
                            0,
                            _recurse_count,
                            _rank_latest_row_number,
                            ranks_by_row_number,
                            {-1: node_index},
                            node_tuples,
                        )

        # Step 2 of the algorithm: apply rank 0 to the blocks that don't yet
        # have a rank
        for node_tuple in reverse_order_nodes:
            if ranks_by_row_number[node_tuple[1]] == -1:
                NodeHandler.recursiveRankInputsIfNotRank0(
                    node_tuple[1],
                    0,
                    _recurse_count,
                    _rank_latest_row_number,
                    ranks_by_row_number,
                    {},
                    node_tuples,
                )

        # Now build the groups based on these ranks
        ranks_given = set(ranks_by_row_number.values())
        new_execution_order_groups = [ExecutionOrderGroup() for i in ranks_given]

        for i, execution_order_group in enumerate(new_execution_order_groups):
            execution_order_group.group_number = i + 1
            execution_order_group.nodes = [
                node_tuple[0]
                for node_tuple in node_tuples
                if ranks_by_row_number[node_tuple[1]] == max(ranks_given) - i
            ]

        return new_execution_order_groups

    @staticmethod
    def getInputNodeIdx(ninput, node_tuples):
        """
        Get the input node for a given input socket and return it's index
        in a tuple list of nodes and indexes
        """
        start_socket = (
            ninput.edges[0].end_socket
            if ninput.edges[0].start_socket.node == ninput.node
            else ninput.edges[0].start_socket
        )
        start_node = start_socket.node

        return next((a[1] for a in node_tuples if a[0] == start_node), None)

    @staticmethod
    def getNodeByIdx(node_tuples, idx):
        """
        Get node from idx in node_tuples list
        """
        return next((a[0] for a in node_tuples if a[1] == idx), None)

    # This function is a replication from a old system - it should remain unchanged at all costs
    @staticmethod
    def repositionSpecificNodes(nodes, offsets=None, starting_position=None): # pylint: disable=R0914,R0912,R0915,R1710
        """
        This function can clean our diagram based on execution groups
        - The primary usage of this function is to do clean_diagram. This
        is because it inherently expects all nodes to exist within the display scene
        as it uses the nodes to access the scene towards the end for assessing
        the positioning comparatively to the scene.
        """
        # Initial starting settings
        last_group_column = -1
        further_open_node_offset = [250.0, 250.0]
        additional_node_offset = [255.0, 250.0]
        starting_node_position = [10, 10]

        if offsets is not None:
            further_open_node_offset = offsets
            additional_node_offset = offsets
        if starting_position is not None:
            starting_node_position = starting_position

        execution_order_groups = NodeHandler.getExecutionGroups(nodes)
        block_linked_pairs = NodeHandler.getLinkedBlocks(nodes)
        if len(nodes) == 0:
            return

        def sorter(x):
            return x.group_number
        groups_dict = dict(enumerate(sorted(execution_order_groups, key=sorter)))
        column_positions = {i: {} for i in groups_dict}
        max_group_column = max(column_positions)

        def closestEmptyPosition(position_float, group_column):
            closest_position = int(position_float + 0.5)
            i = 0
            while (
                closest_position + (i // 2) * (-1 if i % 2 else 1)
            ) in column_positions[group_column]:
                i += 1
            return closest_position + (i // 2) * (-1 if i % 2 else 1)

        for group_column in reversed(sorted(groups_dict)):
            group = groups_dict[group_column]
            def groupGet(x):
                return -len(list(x)[-1])
            if group_column == max_group_column:
                for i, node in enumerate(group.nodes):
                    column_positions[group_column][i] = node
            else:
                nodes_and_connections_in_next_group = sorted(
                    [
                        (
                            node,
                            [
                                block_to
                                for block_from, block_to in block_linked_pairs
                                if block_from is node
                                and block_to in groups_dict[last_group_column].nodes
                            ],
                        )
                        for node in group.nodes
                    ],
                    key=groupGet,
                )

                nodes_and_average_positions = [
                    (
                        node,
                        float("nan")
                        if len(connections) == 0
                        else sum(
                                next(iter((row_position for (row_position, node)
                                          in column_positions[last_group_column].items()
                                         if node is block_to))) for block_to in connections
                        ) / len(connections)
                    )
                    for node, connections in nodes_and_connections_in_next_group
                ]

                for (
                    node,
                    average_position_of_connections,
                ) in nodes_and_average_positions:
                    if not math.isnan(average_position_of_connections):
                        column_positions[group_column][
                            closestEmptyPosition(
                                average_position_of_connections, group_column
                            )
                        ] = node
                if len(column_positions[group_column]):
                    average_row_position = sum(
                        column_positions[group_column].keys()
                    ) / len(column_positions[group_column])
                else:
                    average_row_position = sum(
                        column_positions[last_group_column].keys()
                    ) / len(column_positions[last_group_column])
                for (
                    node,
                    average_position_of_connections,
                ) in nodes_and_average_positions:
                    if math.isnan(average_position_of_connections):
                        column_positions[group_column][
                            closestEmptyPosition(average_row_position, group_column)
                        ] = node

            if len(group.nodes):
                last_group_column = group_column

        # First find the width and height of each column and row based on whether
        # anything is open in them
        open_columns = set()
        rows_in_use = set()
        open_rows = set()
        for column, nodes_by_position_row in column_positions.items():
            for row, node in nodes_by_position_row.items():
                rows_in_use.add(row)

        # Then position based on what rows and columns are open, and put the
        # first item in the first column in the top left of the node_editor

        x_tracker = starting_node_position[0]
        column_x_locations = {}
        for column in column_positions:
            column_x_locations[column] = x_tracker
            x_tracker += additional_node_offset[0]
            if column in open_columns:
                x_tracker += further_open_node_offset[0]

        y_tracker = starting_node_position[0]
        row_y_locations = {}
        for row in rows_in_use:
            row_y_locations[row] = y_tracker
            y_tracker += additional_node_offset[1]
            if row in open_rows:
                y_tracker += further_open_node_offset[1]

        calculatedHeight = (max(row_y_locations.values())) + (
            further_open_node_offset[1] * 10
        )
        calculatedWidth = (max(column_x_locations.values())) + (
            further_open_node_offset[0] * 10
        )
        sceneHeight = (
            calculatedHeight
            if calculatedHeight > node.scene.scene_height
            else node.scene.scene_height
        )
        sceneWidth = (
            calculatedWidth
            if calculatedWidth > node.scene.scene_width
            else node.scene.scene_width
        )

        node.scene.scene_width = sceneWidth
        node.scene.scene_height = sceneHeight
        node.scene.grScene.setGrScene(sceneWidth, sceneHeight)

        for column, nodes_by_position_row in column_positions.items():
            for row, node in nodes_by_position_row.items():
                # column, row = execution_order_group.group_number-1, position_within_group
                node_position = [column_x_locations[column], row_y_locations[row]]
                if column in open_columns:
                    node_position[0] += further_open_node_offset[0] * 0.6
                if row in open_rows:
                    node_position[1] += further_open_node_offset[1] * 0.4
                NodeHandler.setItemPos(node, node_position)

        return node_position[0]

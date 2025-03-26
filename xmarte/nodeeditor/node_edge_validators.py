# -*- coding: utf-8 -*-
"""
A module containing the Edge Validator functions which can be registered as callbacks to
:class:`~nodeeditor.node_edge.Edge` class.

Example of registering Edge Validator callbacks:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can register validation callbacks once for example on the bottom of node_edge.py file or on the
application start with calling this:

.. code-block:: python

    from nodeeditor.node_edge_validators import *

    Edge.registerEdgeValidator(edge_validator_debug)
    Edge.registerEdgeValidator(edge_cannot_connect_two_outputs_or_two_inputs)
    Edge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_same_node)
    Edge.registerEdgeValidator(edge_cannot_connect_input_and_output_of_different_type)


"""
from nodeeditor.node_edge_validators import print_error

DEBUG = False

def edge_start_socket_must_exist(input: 'Socket', output: 'Socket') -> bool:
    """Edge is invalid if the node it started from was deleted whilst dragging"""
    if input.node.grNode is None or output.node.grNode is None:
        print_error("A connecting node has been deleted")
        return False
    return True
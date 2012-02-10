# (c) Nelen & Schuurmans. GPL licensed, see LICENSE.txt.

"""Module docstring.

This serves as a long usage message.
"""

from models import Put, Riool, Rioolmeting
import logging
import networkx as nx



logger = logging.getLogger(__name__)


def post_process_rmb(graph, obj, prev):
    if obj.suf_record_type == '*RIOO':
        graph.add_node(obj.suf_fk_node1, obj=obj)
        graph.add_node(obj.suf_fk_node2, obj=obj)
    elif obj.suf_record_type == '*MRIO':
        if obj.suf_fk_edge not in graph:
            logger.debug("did not find %s in graph", obj.suf_fk_edge)
            return

    graph.add_node(obj.suf_id, obj=obj)
    obj.update_coordinates(prev)

    if (obj.suf_record_type == '*MRIO' and
        prev.suf_record_type == '*RIOO'):
        ## leaving a manhole and starting an inspection line
        graph.add_edge(prev.node(obj.reference), obj.suf_id)
    elif (obj.suf_record_type == '*MRIO' and
          prev.suf_record_type == '*MRIO'):
        ## following an inspection line
        graph.add_edge(prev.suf_id, obj.suf_id)
    elif (obj.suf_record_type == '*RIOO' and
          prev is not None and
          prev.suf_record_type == '*MRIO' and
          prev.suf_fk_edge in graph):
        ## previous inspection line ended and its supporting edge was
        ## completely specified (current obj is possibly unrelated to
        ## it).
        referenced_segment = graph.node[prev.suf_fk_edge]['obj']
        opposite_end = referenced_segment.node(
            prev.reference,
            opposite=True)
        graph.add_edge(prev.suf_id, opposite_end)


def post_process_rib(graph, obj, prev):
    pass


def parse(file_name, objects=[]):
    ""

    classes = {
        ## '*ALGE': None,  # no action
        '*MRIO': Rioolmeting,
        '*PUT': Put,
        '*RIOO': Riool,
        ## '*WAAR': None,  # no action
        }

    prev_obj = None
    global graph
    graph = nx.Graph()
    with open(file_name) as f:
        ## using `with` makes sure the file is closed.
        for i, line in enumerate(f):
            line_no = i + 1
            line = line.strip("\r\n")
            record_type = line.split('|')[0]
            if record_type not in classes:
                continue
            obj = (classes[record_type].
                   parse_line_from_rioolbestand(line, line_no))
            if obj is not None:
                if file_name.lower().endswith('.rmb'):
                    post_process_rmb(graph, obj, prev_obj)
                elif file_name.lower().endswith('.rib'):
                    post_process_rib(graph, obj, prev_obj)

                objects.append(obj)
                prev_obj = obj

    return graph


def main(options, args):
    """
    """

    for file_name in args:
        parse(file_name)


if __name__ == '__main__':
    from optparse import OptionParser
    usage = "usage: %prog [options] input_files..."
    parser = OptionParser(usage=usage)
    (options, args) = parser.parse_args()

    main(options, args)

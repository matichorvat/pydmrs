import re
import itertools
import xml.etree.ElementTree as xml

from graph import load_xml, dump_xml, Edge


def cycle_remove(dmrs_xml, debug=False, cnt=None):
    """
    Iteratively remove cycles from graph by 1) checking if they match any of the specific patterns and 2) cutting the
    edge specified by the pattern. If no pattern can be matched against the cycle, remove it by using the default pattern.
    :param dmrs_xml: DMRS XML object
    :param debug: Print information about detected cycles and matched patterns
    :param cnt: If debug is True, needs to be instantiated Counter object to track pattern occurrences
    :return:
    """

    dmrs_graph = load_xml(dmrs_xml)

    has_cycle = False
    def_or_not_broken = False

    while True:
        cycle = dmrs_graph.contains_cycle()
        if not cycle:
            break

        if debug:
            has_cycle = True
            cnt['cycle'] += 1

        if process_conjunction_index(dmrs_graph, cycle):
            if debug:
                reent_debug(dmrs_graph, cycle, 'CONJ_INDEX')
                cnt['conj_index'] += 1

            continue

        if process_eq(dmrs_graph, cycle):
            if debug:
                reent_debug(dmrs_graph, cycle, 'EQ_')
                cnt['eq'] += 1

            continue

        if process_control(dmrs_graph, cycle):
            if debug:
                reent_debug(dmrs_graph, cycle, 'CONTROL_')
                cnt['control'] += 1

            continue

        # if process_object_control(dmrs_graph, cycle):
        #     if debug:
        #         reent_debug(dmrs_graph, cycle, 'OBJ_CONTROL_')
        #         cnt['obj_control'] += 1
        #
        #     continue

        if process_small_clause(dmrs_graph, cycle):
            if debug:
                reent_debug(dmrs_graph, cycle, 'SMALL_CLAUSE')
                cnt['small_clause'] += 1

            continue

        if process_conjunction_verb_or_adj(dmrs_graph, cycle):
            if debug:
                reent_debug(dmrs_graph, cycle, 'CONJ_VERB_OR_ADJ')
                cnt['conj_verb_or_adj'] += 1

            continue

        if process_default(dmrs_graph, cycle):
            if debug:
                reent_debug(dmrs_graph, cycle, 'DEFAULT_')
                cnt['default'] += 1
                def_or_not_broken = True

            continue

        # Cycle could not be broken
        if debug:
            reent_debug(dmrs_graph, cycle, 'NONE_DETECTED')
            cnt['none_detected'] += 1
            def_or_not_broken = True

        break

    if debug and has_cycle:
        cnt['has_cycle'] += 1

    if debug and def_or_not_broken:
        cnt['def_or_not_broken'] += 1

    return dump_xml(dmrs_graph)


def process_eq(graph, cycle, cut=True):
    """
    Match a cycle if there is an EQ edge that connects two nodes in the cycle. EQ edge is removed if cut is set to True.
    :param graph: DmrsGraph object
    :param cycle: Set of Node objects in the cycle
    :param cut: If True and cycle is matched, the cycle is broken by removing a target edge
    :return: True if cycle is matched, otherwise False
    """

    for node in cycle:
        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(node) if edge.to_node in cycle]
        outgoing_labels = dict((edge.label, edge) for edge in outgoing_edges)

        if 'EQ' not in outgoing_labels:
            continue

        if cut:
            graph.edges.remove(outgoing_labels['EQ'])

        return True

    return False


def process_control(graph, cycle, cut=True):
    """
    Match a cycle if there is a control relationship: verb with an incoming edge of ARG N / H, where N != 1,
    and an outgoing edge ARG1/NEQ; or if there is an ARG1_H incoming edge from neg_rel node, and neg_rel node has
    an incoming edge of ARG N / H, where N != 1. ARG1/NEQ edge is removed if cut is set to True.
    :param graph: DmrsGraph object
    :param cycle: Set of Node objects in the cycle
    :param cut: If True and cycle is matched, the cycle is broken by removing a target edge
    :return: True if cycle is matched, otherwise False
    """

    verb_nodes = [node for node in cycle if node.pos == 'v']

    if len(verb_nodes) == 0:
        return False

    for verb_node in verb_nodes:
        incoming_edges = [edge for edge in graph.get_incoming_node_edges(verb_node) if edge.from_node in cycle]
        incoming_labels = dict((edge.label, edge.from_node) for edge in incoming_edges)
        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(verb_node) if edge.to_node in cycle]

        if not any([re.match(r'ARG[23]_H', edge_label) for edge_label in incoming_labels]):

            if 'ARG1_H' not in incoming_labels:
                continue

            if not incoming_labels['ARG1_H'].gpred == 'neg_rel':
                continue

            neg_incoming_edges = [edge for edge in graph.get_incoming_node_edges(incoming_labels['ARG1_H']) if edge.from_node in cycle]

            if not any([re.match(r'ARG[23]_H', edge.label) for edge in neg_incoming_edges]):
                continue

        if not any([edge.label == 'ARG1_NEQ' for edge in outgoing_edges]):
            continue

        if cut:
            arg1_neq_edge = [edge for edge in outgoing_edges if edge.label == 'ARG1_NEQ'][0]
            graph.edges.remove(arg1_neq_edge)

        return True

    return False


def process_object_control(graph, cycle, cut=True):

    verb_nodes = [node for node in cycle if node.pos == 'v']

    if len(verb_nodes) == 0:
        return False

    for verb_node in verb_nodes:

        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(verb_node) if edge.to_node in cycle]
        outgoing_labels = dict((edge.label, edge.to_node) for edge in outgoing_edges)

        arg2_nodes = [edge_to_node for edge_label, edge_to_node in outgoing_labels.items() if edge_label.startswith('ARG2')]

        if len(arg2_nodes) != 1:
            continue

        if 'ARG3_H' not in outgoing_labels:
            continue

        arg2_node = arg2_nodes[0]
        arg3_node = outgoing_labels['ARG3_H']

        arg3_node_outgoing_edges = graph.get_outgoing_node_edges(arg3_node)

        if not any([True for edge in arg3_node_outgoing_edges if edge.label.startswith('ARG2') and edge.to_node == arg2_node]):
            continue

        return True

    return False


def process_small_clause(graph, cycle, cut=True):
    """
    Match a cycle if there is a small clause relationship: verb with outgoing edge ARG3/H to a preposition node, the
    preposition node has an outgoing edge ARG1/NEQ, and
    1) an outgoing edge ARG2/NEQ, or
    2) an outgoing edge ARG2/EQ to a noun;
    ARG2/NEQ or ARG2/EQ edge is removed if cut is set to True.
    :param graph: DmrsGraph object
    :param cycle: Set of Node objects in the cycle
    :param cut: If True and cycle is matched, the cycle is broken by removing a target edge
    :return: True if cycle is matched, otherwise False
    """

    verb_nodes = [node for node in cycle if node.pos == 'v']

    if len(verb_nodes) == 0:
        return False

    for verb_node in verb_nodes:
        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(verb_node) if edge.to_node in cycle]
        outgoing_labels = dict((edge.label, edge.to_node) for edge in outgoing_edges)

        if 'ARG3_H' not in outgoing_labels:
            continue

        prep_node = outgoing_labels['ARG3_H']

        if prep_node.pos != 'p':
            continue

        prep_outgoing_labels = [edge.label for edge in graph.get_outgoing_node_edges(prep_node) if edge.to_node in cycle]

        if 'ARG1_NEQ' not in prep_outgoing_labels:
            continue

        if 'ARG2_NEQ' in outgoing_labels:

            if cut:
                arg2_neq_edge = [edge for edge in outgoing_edges if edge.label == 'ARG2_NEQ'][0]
                graph.edges.remove(arg2_neq_edge)

            return True

        if 'ARG2_EQ' in outgoing_labels and outgoing_labels['ARG2_EQ'].pos == 'n':

            if cut:
                arg2_eq_edge = [edge for edge in outgoing_edges if edge.label == 'ARG2_EQ'][0]
                graph.edges.remove(arg2_eq_edge)

            return True

    return False


def is_conj(node):
    return node.pos == 'c' or node.gpred is not None and node.gpred.startswith('implicit_conj')


def process_conjunction_verb_or_adj(graph, cycle, cut=True):
    """
    Match a cycle if there is a conjunction of verbs or adjectives: conjunction of two verbs or two adjectives and those
    two verbs or two adjectives in turn connect to at least one shared node. Edges from two verbs or adjectives to shared
    nodes are removed if cut is set to True and replaced by an edge going to the same shared node but originating from the
    conjunction node.
    :param graph: DmrsGraph object
    :param cycle: Set of Node objects in the cycle
    :param cut: If True and cycle is matched, the cycle is broken by removing a target edge
    :return: True if cycle is matched, otherwise False
    """

    conj_nodes = [node for node in cycle if is_conj(node)]

    if len(conj_nodes) == 0:
        return False

    for conj_node in conj_nodes:
        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(conj_node) if edge.to_node in cycle]
        verb_or_adj_nodes = list(set([edge.to_node for edge in outgoing_edges if edge.to_node.pos == 'v' or edge.to_node.pos == 'a']))

        if len(verb_or_adj_nodes) != 2:
            continue

        verb_or_adj_0_outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(verb_or_adj_nodes[0]) if edge.to_node in cycle]
        verb_or_adj_1_outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(verb_or_adj_nodes[1]) if edge.to_node in cycle]

        verb_or_adj_0_outgoing_adjacent_nodes = set(edge.to_node for edge in verb_or_adj_0_outgoing_edges)
        verb_or_adj_1_outgoing_adjacent_nodes = set(edge.to_node for edge in verb_or_adj_1_outgoing_edges)

        common_outgoing_nodes = verb_or_adj_0_outgoing_adjacent_nodes & verb_or_adj_1_outgoing_adjacent_nodes

        if len(common_outgoing_nodes) == 0:
            continue

        if cut:
            edge_distances = []
            for node in common_outgoing_nodes:
                for edge in graph.get_incoming_node_edges(node):
                    #print edge.from_node.tokalign, edge.to_node.tokalign
                    if edge.from_node not in verb_or_adj_nodes or not edge.from_node.tokalign or not edge.to_node.tokalign:
                        continue

                    edge_distance = min([abs(x - y) for x, y in itertools.product(edge.from_node.tokalign, edge.to_node.tokalign)])
                    edge_distances.append((edge_distance, edge))


            edge_distances = sorted(edge_distances, key=lambda x: x[0])

            for _, edge in edge_distances[1:]:
                graph.edges.remove(edge)

        return True

    return False


def process_conjunction_index(graph, cycle, cut=True):
    """
    Match a cycle if edges (HNDL and INDEX) of either side of a conjunction (right or left) connect to different nodes.
    INDEX edge is removed if cut is set to True.
    :param graph: DmrsGraph object
    :param cycle: Set of Node objects in the cycle
    :param cut: If True and cycle is matched, the cycle is broken by removing a target edge
    :return: True if cycle is matched, otherwise False
    """

    conj_nodes = [node for node in cycle if is_conj(node)]

    if len(conj_nodes) == 0:
        return False

    # Find conjunction nodes that have index and handel pointing to different nodes
    for conj_node in conj_nodes:
        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(conj_node) if edge.to_node in cycle]
        outgoing_labels = dict((edge.label.split('_')[0], edge.to_node) for edge in outgoing_edges)

        detected = False

        if 'R-INDEX' in outgoing_labels and 'R-HNDL' in outgoing_labels and outgoing_labels['R-INDEX'] != outgoing_labels['R-HNDL']:
            detected = True

            if cut:
                r_index_edge = [edge for edge in outgoing_edges if edge.label.startswith('R-INDEX')][0]
                graph.edges.remove(r_index_edge)

        if 'L-INDEX' in outgoing_labels and 'L-HNDL' in outgoing_labels and outgoing_labels['L-INDEX'] != outgoing_labels['L-HNDL']:
            detected = True

            if cut:
                l_index_edge = [edge for edge in outgoing_edges if edge.label.startswith('L-INDEX')][0]
                graph.edges.remove(l_index_edge)

        if detected:
            return True

    return False


def process_default(graph, cycle, cut=True):
    """
    Match any cycle and remove the edge which spans the longest distance between tokens associated with the nodes it connects.
    :param graph: DmrsGraph object
    :param cycle: Set of Node objects in the cycle
    :param cut: If True and cycle is matched, the cycle is broken by removing a target edge
    :return: True if cycle is matched, otherwise False
    """

    cycle_edges = []
    for node in cycle:
        outgoing_edges = [edge for edge in graph.get_outgoing_node_edges(node) if edge.to_node in cycle]
        cycle_edges.extend(outgoing_edges)

    edge_distances = []
    for edge in cycle_edges:
        if not edge.from_node.tokalign or not edge.to_node.tokalign:
            continue

        edge_distance = min([abs(x - y) for x, y in itertools.product(edge.from_node.tokalign, edge.to_node.tokalign)])
        edge_distances.append((edge_distance, edge))

    if len(edge_distances) > 0:
        if cut:
            max_distance_edge = max(edge_distances)[1]
            graph.edges.remove(max_distance_edge)

        return True

    return False


def reent_debug(graph, cycle, reent_type):

    print reent_type
    print ','.join(node.label.encode('utf-8') for node in cycle)
    print graph.attrib.get('untok').encode('utf-8')
    print '*' * 20

    for node in cycle:
        print node.label.encode('utf-8')

        for edge in graph.get_outgoing_node_edges(node):

            if edge.to_node not in cycle:
                continue

            print '-' + edge.label.encode('utf-8') + '->', edge.to_node.label.encode('utf-8')

        print '*' * 20

    print xml.tostring(dump_xml(graph))
    print '*' * 100


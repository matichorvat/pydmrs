from collections import defaultdict


def curb_gpred_spans(dmrs_xml, max_tokens=3):
    '''
    Remove general predicate node token alignments if a general predicate node spans more than max_tokens.
    This prevents general predicate nodes from dominating rule extraction.
    :param dmrs_xml: Input DMRS XML
    :param max_tokens: Maximum number of allowed tokens before the entire general predicate node span is removed
    :return: Modified DMRS
    '''

    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        # Determine if the node is a general predicate
        gpred_node = False
        for node_info in entity:
            if node_info.tag == 'gpred':
                gpred_node = True
                break

        if not gpred_node:
            continue

        # Remove the alignment if the number of tokens exceeds the specified limit
        tokalign = entity.attrib.get('tokalign')
        gpred_token_num = len(tokalign.split(' '))

        if gpred_token_num > max_tokens:
            entity.attrib['tokalign'] = ''

    return dmrs_xml


def filter_gpred(dmrs_xml, gpred_filter, handle_ltop=True, allow_disconnected_dmrs=False):
    """
    Remove general predicate nodes on the filter list from the DMRS.
    :param dmrs_xml: Input DMRS XML
    :param gpred_filters: A set of general predicates to filter
    :param handle_ltop: Boolean indicating whether to reassign ltop from filtered gpred
    :param allow_disconnected_dmrs: Remove gpred nodes even if their removal would result in a disconnected DMRS.
     If DMRS was already disconnected, gpred nodes are removed regardless.
    :return: Modified DMRS XML
    """

    dmrs_graph, filterable_nodes = parse_dmrs_xml(dmrs_xml, gpred_filter)

    test_connectedness = not allow_disconnected_dmrs and is_connected(dmrs_graph, ignored_nodeids=filterable_nodes)

    # If DMRS should remain connected, check that removing filterable nodes will not result in a disconnected DMRS
    if test_connectedness:
        filtered_nodes = set()
        for node in filterable_nodes:
            if is_connected(dmrs_graph, removed_nodeids=filtered_nodes | {node}, ignored_nodeids=filterable_nodes):
                filtered_nodes.add(node)

    else:
        filtered_nodes = filterable_nodes

    if handle_ltop and dmrs_xml.attrib.get('ltop') in filtered_nodes:
        new_ltop = choose_new_ltop(dmrs_xml, dmrs_graph, filtered_nodes)

        if new_ltop is not None:
            dmrs_xml.attrib['ltop'] = new_ltop

    # Remove filtered nodes and their links from the DMRS
    remove_filtered_nodes(dmrs_xml, filtered_nodes)

    return dmrs_xml


def parse_dmrs_xml(dmrs_xml, gpred_filter):
    """
    Parse DMRS XML to node and edge sets and identify filterable_nodes.
    :param dmrs_xml: DMRS XML object
    :param gpred_filter: A set of general predicates to filter
    :return: ((nodes, undirected_edges, directed_edges), filterable_nodes) tuples
    """

    nodes = set()
    undirected_edges = defaultdict(set)
    directed_edges = defaultdict(set)
    filterable_nodes = set()

    for entity in dmrs_xml:
        if entity.tag == 'node':
            node_id = entity.attrib['nodeid']
            nodes.add(node_id)

            gpred_rel = gpred_node(entity)
            if gpred_rel is not None and gpred_rel in gpred_filter:
                filterable_nodes.add(node_id)

        if entity.tag == 'link':
            link_from = entity.attrib['from']
            link_to = entity.attrib['to']

            undirected_edges[link_from].add(link_to)
            undirected_edges[link_to].add(link_from)
            directed_edges[link_from].add(link_to)

    return (nodes, undirected_edges, directed_edges), filterable_nodes


def gpred_node(node_xml):
    """
    Get gpred node info if it exists, otherwise return None
    :param node_xml: Node XML object
    :return: grep_rel string or None
    """

    for node_info in node_xml:
        if node_info.tag == 'realpred':
            return None
        elif node_info.tag == 'gpred':
            return node_info.text

    return None


def is_connected(dmrs_graph, removed_nodeids=frozenset(), ignored_nodeids=frozenset()):
    """
    Determine if a DMRS graph is connected.
    :param dmrs_graph: Tuple of sets (nodes, undirected_edges, directed_edges)
    :param removed_nodeids: Set of node ids that should be considered as already removed.
     This is to prevent the need for excessive copying of DMRS graphs for hypothetical node removals.
    :param ignored_nodeids: Set of node ids that should not be considered as disconnected if found as such.
     This is to prevent nodes that are going to be filtered out later from affecting results of connectivity test.
    :return: True if DMRS is connected, otherwise False.
    """
    disconnected = compute_disconnected_nodeids(dmrs_graph, removed_nodeids=removed_nodeids)
    return len(disconnected - ignored_nodeids) == 0


def compute_disconnected_nodeids(dmrs_graph, removed_nodeids=frozenset()):
    """
    Search for disconnected nodes.
    :param dmrs_graph: Tuple of sets (nodes, undirected_edges, directed_edges)
    :param removed_nodeids: Set of node ids that should be considered as already removed.
     This is to prevent the need for excessive copying of DMRS graphs for hypothetical node removals.
    :return: Set of disconnected node ids
    """

    # Operate on undirected edges
    nodes, edges, _ = dmrs_graph

    # Initialize the set of node that have not been visited yet
    unvisited_nodeids = set(nodes) - removed_nodeids
    if not unvisited_nodeids:
        return unvisited_nodeids

    start_id = next(iter(unvisited_nodeids))

    # Start the explore set with nodes adjacent to the starting node
    explore_set = get_neighbours(start_id, edges) & unvisited_nodeids
    unvisited_nodeids.remove(start_id)

    # Iteratively visit a node and update the explore set with neighbouring nodes until explore set empty
    while explore_set:
        node = explore_set.pop()
        unvisited_nodeids.remove(node)
        explore_set.update(get_neighbours(node, edges) & unvisited_nodeids)

    return unvisited_nodeids


def get_neighbours(node, edges):
    return edges[node]


def choose_new_ltop(dmrs_xml, dmrs_graph, filtered_nodes):
    """
    Choose the new LTOP because old LTOP is being filtered out.
    :param dmrs_xml: DMRS XML object
    :param dmrs_graph: Tuple of sets (nodes, undirected_edges, directed_edges)
    :param filtered_nodes: List of nodes to filter
    """

    ltop = dmrs_xml.attrib.get('ltop')
    index = dmrs_xml.attrib.get('index')

    # Operate on directed edges
    nodes, undirected_edges, edges = dmrs_graph

    # Iteratively search for new ltop
    while True:

        # Try to select it from previous ltop children
        ltop_children = list(get_neighbours(ltop, edges))

        # If only one child exists and it hasn't been filtered, choose it as new ltop
        if len(ltop_children) == 1 and ltop_children[0] not in filtered_nodes:
            return ltop_children[0]

        # Or if multiple children exist and one of them equals to index, choose it as new ltop
        elif index in ltop_children:
            return index

        # Try to select it from previous ltop parents
        ltop_parents = list(get_neighbours(ltop, undirected_edges) - get_neighbours(ltop, edges))

        # If only one parent exists and it hasn't been filtered, choose it as new ltop
        if len(ltop_parents) == 1 and ltop_parents[0] not in filtered_nodes:
            return ltop_parents[0]

        # If only one child exists and it has been filtered, choose it as temporary ltop and iterate
        if len(ltop_children) == 1:
            ltop = ltop_children[0]
            continue

        # If only one parent exists and it has been filtered, choose it as temporary ltop and iterate
        if len(ltop_parents) == 1:
            ltop = ltop_parents[0]
            continue

        break

    # As a last resort, choose a random unfiltered node, if it exists
    if len(nodes - filtered_nodes) > 0:
        return set(nodes - filtered_nodes).pop()

    else:
        return None


def remove_filtered_nodes(dmrs_xml, filtered_nodes):
    """
    Remove nodes on filtered_nodes list and associated links from dmrs_xml.
    :param dmrs_xml: DMRS XML object
    :param filtered_nodes: List of nodes to filter
    """

    entities_to_remove = []

    for entity in dmrs_xml:
        if entity.tag == 'node':
            node_id = entity.attrib['nodeid']
            if node_id in filtered_nodes:
                entities_to_remove.append(entity)

        if entity.tag == 'link':
            link_from = entity.attrib['from']
            link_to = entity.attrib['to']

            if link_from in filtered_nodes or link_to in filtered_nodes:
                entities_to_remove.append(entity)

    for entity in entities_to_remove:
        dmrs_xml.remove(entity)


def parse_gpred_filter_file(filename):
    filter_out = set()
    filter_in = set()

    with open(filename, 'rb') as f:

        for line in f:
            line = line.strip()

            if line == '' or line == '#':
                continue

            entry = line.split('\t')

            assert len(entry) == 2

            if entry[1] == 'yes':
                filter_in.add(entry[0])
            elif entry[1] == 'no':
                filter_out.add(entry[0])
            else:
                raise Exception('Unknown option: %s' % line)

    return filter_out
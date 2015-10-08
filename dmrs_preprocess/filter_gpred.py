from collections import defaultdict


def parse_gpred_filter_file(filename):
    filter_out = set()
    filter_in = set()

    with open(filename, 'rb') as f:
        yes = no = False

        for line in f:
            line = line.strip()

            if line == '' or line == '#':
                continue
            elif line.startswith('KEEP'):
                yes = True
            elif line.startswith('FILTER'):
                no = True
                yes = False
            elif yes:
                filter_in.add(line)
            elif no:
                filter_out.add(line)

    return filter_out


def filter_gpred(dmrs_xml, gpred_filter):
    '''
    Remove general predicate nodes on the filter list from the DMRS.
    :param dmrs_xml: Input DMRS XML
    :param gpred_filters: A set of general predicates to filter
    :return: Modified DMRS XML
    '''
    remove_nodes = dict()
    remove_links = set()

    # Find general predicate nodes to filter
    for entity in dmrs_xml:
        if entity.tag == 'node':
            node = entity
            node_id = node.attrib['nodeid']
            gpred_rel = None

            for node_info in node:
                if node_info.tag == 'realpred':
                    break
                elif node_info.tag == 'gpred':
                    gpred_rel = node_info.text
                    break

            if gpred_rel and gpred_rel in gpred_filter:
                remove_nodes[node_id] = node

    # Test whether removing a node would result in a disconnected graph. Remove only the ones that do not.
    removed_nodes = dict()
    removed_node_ids = set()

    already_disconnected = not is_connected(dmrs_xml)

    for node_id, node in remove_nodes.items():
        if not already_disconnected and not is_connected(dmrs_xml, removed_nodes=(removed_node_ids | {node_id}), to_remove=remove_nodes):
            #print 'Removing node with id %s would result in a disconnected graph, so we are not.' % node_id
            continue
        else:
            removed_node_ids.add(node_id)
            removed_nodes[node_id] = node

    # Actually remove nodes
    for _, node in removed_nodes.items():
        dmrs_xml.remove(node)

    # Find links to or from general predicate nodes to filter
    for entity in dmrs_xml:
        if entity.tag == 'link':
            link = entity
            if link.attrib['from'] in removed_nodes or link.attrib['to'] in removed_nodes:
                remove_links.add(link)

    for link in remove_links:
        dmrs_xml.remove(link)

    return dmrs_xml


def is_connected(dmrs_xml, removed_nodes=None, to_remove=None):
    """Determine if a DMRS graph is connected."""
    graph = get_graph(dmrs_xml, removed_nodes)
    disconnected_nodes = bf(graph)

    if to_remove is not None:
        disconnected_nodes -= set(to_remove)

    return True if len(disconnected_nodes) == 0 else False


def get_graph(dmrs_xml, removed_nodes=None):
    """Obtain a graph representation of the DMRS"""

    nodes = set()
    links = defaultdict(set)

    if removed_nodes is None:
        removed_nodes = set()

    for entity in dmrs_xml:

        if entity.tag == 'node':
            node_id = entity.attrib['nodeid']

            if node_id not in removed_nodes:
                nodes.add(node_id)

        if entity.tag == 'link':
            link_from = entity.attrib['from']
            link_to = entity.attrib['to']

            # Simulate that the graph already has nodes removed
            if link_from not in removed_nodes and link_to not in removed_nodes:
                links[link_from].add(link_to)
                links[link_to].add(link_from)

    return nodes, links


MAX_ITER = 100

def bf(graph):
    """Breadth-first search of the graph for disconnected nodes."""
    nodes, links = graph
    unvisited = set(nodes)

    if len(nodes) == 0:
        return unvisited

    # Select a random starting node to visit
    start_node = next(iter(nodes))
    unvisited.remove(start_node)

    # Start the explore list with nodes adjacent to the starting node
    explore_list = set(links[start_node])

    cur_iter = 0
    while len(explore_list) > 0:

        if cur_iter >= MAX_ITER:
            break

        new_explore_list = set()

        for node in explore_list:
            unvisited.remove(node)
            new_explore_list.update(links[node])

        explore_list = filter(lambda x: x in unvisited, new_explore_list)
        cur_iter += 1

    return unvisited


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

import xml.etree.ElementTree as xml


class DmrsGraph(object):

    def __init__(self, nodes, edges, attrib):
        self.nodes = set(nodes)
        self.edges = set(edges)
        self.attrib = attrib

    def get_outgoing_node_edges(self, node):
        return [edge for edge in self.edges if edge.from_node.node_id == node.node_id]

    def get_incoming_node_edges(self, node):
        return [edge for edge in self.edges if edge.to_node.node_id == node.node_id]

    def get_incident_edges(self, node):
        return self.get_outgoing_node_edges(node) + self.get_incoming_node_edges(node)

    def get_child_nodes(self, node):
        return [edge.to_node for edge in self.get_outgoing_node_edges(node)]

    def get_parent_nodes(self, node):
        return [edge.from_node for edge in self.get_incoming_node_edges(node)]

    def get_adjacent_nodes(self, node):
        return self.get_child_nodes(node) + self.get_parent_nodes(node)

    def contains_directed_cycle(self):
        """
        Check whether the graph contains a directed cycle by iteratively removing nodes that either have no parents or no children.
         When no nodes can be removed from the remaining list, the graph has a cycle.
        :return: Set of Node objects in the cycle or empty set if no cycle exists.
        """

        nodes_from = dict((node, set(self.get_child_nodes(node))) for node in self.nodes)
        nodes_to = dict((node, set(self.get_parent_nodes(node))) for node in self.nodes)

        remaining_nodes = set(self.nodes)
        has_node_been_removed = True

        while has_node_been_removed:
            has_node_been_removed = False

            for node in remaining_nodes:
                # If node has no children, remove it
                if len(nodes_from[node] & remaining_nodes) == 0:
                    remaining_nodes.remove(node)
                    has_node_been_removed = True
                    break

                # If node has no parents, remove it
                elif len(nodes_to[node] & remaining_nodes) == 0:
                    remaining_nodes.remove(node)
                    has_node_been_removed = True
                    break

        return remaining_nodes

    def contains_undirected_cycle(self):
        """
        Check whether the graph contains an undirected cycle by iteratively removing nodes that have a single adjacent node.
         When no nodes can be removed from the remaining list, the graph has a cycle.
        :return: Set of Node objects in the cycle or empty set if no cycle exists.
        """

        adjacent_nodes = dict((node, set(self.get_adjacent_nodes(node))) for node in self.nodes)

        remaining_nodes = set(self.nodes)
        has_node_been_removed = True

        while has_node_been_removed:
            has_node_been_removed = False

            for node in remaining_nodes:
                # If node has a single adjacent node, remove it
                if len(adjacent_nodes[node] & remaining_nodes) <= 1:
                    remaining_nodes.remove(node)
                    has_node_been_removed = True
                    break

        return remaining_nodes

    def contains_cycle(self):
        """
        Checks whether the graph contains any cycle, directed or undirected.
        :return: Set of Node objects in the cycle or empty set if no cycle exists. Directed cycles are given priority.
        """
        directed_cycle = self.contains_directed_cycle()

        if directed_cycle:
            return directed_cycle

        undirected_cycle = self.contains_undirected_cycle()

        if undirected_cycle:
            return undirected_cycle

        return set()


class Node(object):

    def __init__(self, node_id, label, tokalign, xml_entity, lemma=None, sense=None, pos=None, gpred=None):
        self.node_id = node_id
        self.label = label
        self.tokalign = {} if tokalign is None else tokalign
        self.xml_entity = xml_entity

        self.lemma = lemma
        self.sense = sense
        self.pos = pos
        self.gpred = gpred

    def __str__(self):
        return str(self.node_id)

    def __repr__(self):
        return "Node(id=%r,label=%r)" % (self.node_id, self.label)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, Node):
            return (self.node_id == other.node_id) and (self.label == other.label)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        return cmp(int(self.node_id), int(other.node_id))


class Edge(object):

    def __init__(self, from_node, to_node, label, xml_entity):
        self.from_node = from_node
        self.to_node = to_node
        self.label = label
        self.xml_entity = xml_entity

    @property
    def edge_id(self):
        return "%s,%s,%s" % (self.from_node, self.to_node, self.label)

    @property
    def string(self):
        return "%s,%s,%s" % (self.from_node.label, self.to_node.label, self.label)

    def __str__(self):
        return str(self.edge_id)

    def __repr__(self):
        return "Edge(fromNode=%r,toNode=%r,label=%r)" % \
               (self.from_node, self.to_node, self.label)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if isinstance(other, Edge):
            return (self.from_node == other.from_node) and \
                   (self.to_node == other.to_node) and \
                   (self.label == other.label)
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __cmp__(self, other):
        if cmp(self.from_node, other.from_node):
            return cmp(self.from_node, other.from_node)

        elif cmp(self.to_node, other.to_node):
            return cmp(self.to_node, other.to_node)

        elif cmp(self.label, other.label):
            return cmp(self.label, other.label)

        else:
            return 0


def load_xml(dmrs_xml):
    """
    Load a DMRS XML graph representation into DmrsGraph object consisting of Nodes and Edges.
    """

    nodes = {}
    edges_raw = []

    for element in dmrs_xml:

        if element.tag == 'node':
            node_id = element.attrib.get('nodeid')

            label = element.attrib.get('label')

            tokalign = element.attrib.get('tokalign')

            if tokalign == '-1' or tokalign is None:
                tokalign = []
            else:
                tokalign = [int(tok) for tok in tokalign.split(' ') if tok != '']

            kwargs = {}

            if element.findall('realpred'):
                realpred = element.findall('realpred')[0] if element.findall('realpred') else None

                kwargs['lemma'] = realpred.attrib.get('lemma')
                kwargs['sense'] = realpred.attrib.get('sense')
                kwargs['pos'] = realpred.attrib.get('pos')

            elif element.findall('gpred'):
                kwargs['gpred'] = element.findall('gpred')[0].text if element.findall('gpred') else None

            nodes[node_id] = Node(node_id, label, tokalign, element, **kwargs)

        elif element.tag == 'link':

            node_from = element.attrib.get('from')
            node_to = element.attrib.get('to')
            label = element.attrib.get('label')

            edges_raw.append((node_from, node_to, label, element))

    edges = []
    for edge in edges_raw:
        edges.append(Edge(nodes[edge[0]], nodes[edge[1]], edge[2], edge[3]))

    return DmrsGraph(
        nodes.values(),
        edges,
        attrib=dict(dmrs_xml.attrib)
    )


def dump_xml(dmrs_graph):
    dmrs_xml = xml.Element('dmrs')
    dmrs_xml.attrib = dmrs_graph.attrib
    dmrs_xml.text = '\n'
    dmrs_xml.tail = '\n'

    for node in sorted(dmrs_graph.nodes):
        node.xml_entity.tail = '\n'
        dmrs_xml.append(node.xml_entity)

    for edge in sorted(dmrs_graph.edges):
        edge.xml_entity.tail = '\n'
        dmrs_xml.append(edge.xml_entity)

    return dmrs_xml

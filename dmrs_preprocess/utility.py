import random
from itertools import tee, izip

random.seed(0)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def triple(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b, c = tee(iterable, 3)
    next(b, None)
    next(c, None)
    next(c, None)

    return izip(a, b, c)


def contains_sublist(lst, sublst):
    n = len(sublst)
    return any((sublst == lst[i:i+n]) for i in xrange(len(lst)-n+1))


def empty(dmrs_xml):
    for _ in dmrs_xml:
        return False

    return True


def load_wmap(filename):
    wmap = dict()

    with open(filename, 'rb') as fp:
        for line in fp:
            entry = line.strip().split('\t')

            assert len(entry) == 2

            wmap[entry[1]] = int(entry[0])

    return wmap


def strip_source_information(dmrs_xml):
    nodes = []
    edges = []

    # Build dmrs representation and strip source information
    for entity in dmrs_xml:
        if entity.tag == 'node':
            nodes.append(entity)

            del entity.attrib['cfrom']
            del entity.attrib['cto']

        if entity.tag == 'link':
            edges.append(entity)

    # Remove all entities, shuffle them, then readd them to DMRS
    for entity in nodes + edges:
        dmrs_xml.remove(entity)

    # Shuffle
    random.shuffle(nodes)
    random.shuffle(edges)

    # Remap nodeids according to the shuffled order and readd them to DMRS XML
    nodeid_map = {}
    for index, node in enumerate(nodes):
        nodeid = str(10000 + index)
        nodeid_map[node.attrib['nodeid']] = nodeid
        node.attrib['nodeid'] = nodeid

        dmrs_xml.append(node)

    for edge in edges:
        edge.attrib['from'] = nodeid_map[edge.attrib['from']]
        edge.attrib['to'] = nodeid_map[edge.attrib['to']]
        dmrs_xml.append(edge)

    if dmrs_xml.attrib['ltop'] != '-1':
        dmrs_xml.attrib['ltop'] = nodeid_map[dmrs_xml.attrib['ltop']]

    return dmrs_xml

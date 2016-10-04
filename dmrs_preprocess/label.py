

def create_label(dmrs_xml, carg_clean=False):
    """
    Create an identifying label attribute for each node and link,
    consisting of its arguments and properties.
    :param dmrs_xml: Input DMRS XML
    :return: Modified DMRS XML
    """

    for entity in dmrs_xml:
        if entity.tag == 'node':

            node_attribs = collect_node_attribs(entity)

            if node_attribs.get('gpred') is not None:

                # Remove quotes around CARG
                if node_attribs.get('carg') is not None and carg_clean:
                    clean_carg = node_attribs['carg'][1:-1]
                    entity.attrib['carg'] = clean_carg
                    node_attribs['carg'] = clean_carg

                label = label_gpred(node_attribs)

            elif node_attribs.get('pos') == 'n':
                label = label_noun(node_attribs)

            elif node_attribs.get('pos') == 'v':
                label = label_verb(node_attribs)

            else:
                label = label_default(node_attribs)

            # Attach the label to node XML
            entity.attrib['label'] = label

        elif entity.tag == 'link':
            # Get ARG and POST of a link
            arg = entity.findall('rargname')[0].text if entity.findall('rargname') else None
            post = entity.findall('post')[0].text if entity.findall('post') else None

            # Create a label and attach it to the link XML
            entity.attrib['label'] = '_'.join([x for x in [arg, post] if x is not None])

    return dmrs_xml


def label_gpred(node_attribs):
    label_list = [
        node_attribs.get('carg'),
        node_attribs.get('gpred'),
        node_attribs.get('pers'),
        node_attribs.get('num'),
        node_attribs.get('gend')
    ]

    return '_'.join([unicode(x) for x in label_list if x is not None])


def label_noun(node_attribs):
    label_list = [
        node_attribs.get('lemma'),
        node_attribs.get('pos'),
        node_attribs.get('sense'),
        node_attribs.get('pers') if node_attribs.get('pers') is not None else '3',
        node_attribs.get('num') if node_attribs.get('num') is not None else 'sg'
    ]

    return '_' + '_'.join([unicode(x) for x in label_list if x is not None])


def label_verb(node_attribs):
    label_list = [
        node_attribs.get('lemma'),
        node_attribs.get('pos'),
        node_attribs.get('sense'),
        node_attribs.get('tense'),
        node_attribs.get('sf')
    ]

    return '_' + '_'.join([unicode(x) for x in label_list if x is not None])


def label_default(node_attribs):
    label_list = [
        node_attribs.get('lemma'),
        node_attribs.get('pos'),
        node_attribs.get('sense')
    ]

    return '_' + '_'.join([unicode(x) for x in label_list if x is not None])


def collect_node_attribs(node):
    """
    Collect node attributes in a dictionary
    :param node: XML node
    :return: Dictionary of node attributes
    """

    node_attribs = dict()
    for node_info in node:
        node_attribs.update(node_info.attrib)

        if node_info.tag == 'gpred':
            node_attribs[node_info.tag] = node_info.text

    if node.attrib.get('carg') is not None:
        node_attribs['carg'] = node.attrib['carg']

    if node_attribs.get('tense') is not None and node_attribs.get('tense').lower() == 'untensed':
        del node_attribs['tense']

    if node_attribs.get('sf') == 'prop' or node_attribs.get('sf') == 'prop-or-ques':
        del node_attribs['sf']

    return node_attribs

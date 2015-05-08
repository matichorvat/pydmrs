import xml.etree.ElementTree as xml

from unaligned_tokens_align import get_unaligned_tokens


complex_en = {'.': 'full_stop', '!': 'exclamation_mark', '?': 'question_mark', ',': 'comma',
               ';': 'semicolon', ':': 'colon', '/': 'slash', '\\': 'backward_slash',
               '-': 'minus_dash', u'\u2012': 'figure_dash', u'\u2013': 'en_dash', u'\u2014': 'em_dash',
               u'\u2015': 'horizontal_bar', u'\u2053': 'swung_dash',
               u'\u2018': 'single_opening_quotation_mark',
               u'\u2019': 'apostrophe_or_single_closing_quotation_mark',
               u'\u201C': 'double_opening_quotation_mark', u'\u201D': 'double_closing_quotation_mark',
               '\'': 'typewriter_apostrophe',
               '(': 'left_paranthesis', ')': 'right_parenthesis',
               '[': 'left_square_bracket', ']': 'right_square_bracket',
               '{': 'left_curly_bracket', '}': 'right_curly_bracket'}


def add_punctuation(dmrs_xml, tok, punctuation='complex_en'):
    '''
    Add punctuation nodes and links to DMRS, aligned to punctuation tokens.
    :param dmrs_xml: Input DMRS XML
    :param tok: Input list of tokens
    :param punctuation: Mapping between punctuation characters and the node labels
    :return: Modified DMRS XML with punctuation nodes and links and alignment to tokens
    '''

    if punctuation == 'complex_en':
        punctuation_dict = complex_en
    else:
        raise NotImplementedError('Punctuation dictionary %s not implemented.' % punctuation)

    punc_token_node_links = None

    # Get insertion points for insertion of punctuation nodes and links
    max_node_id, node_insert_position = insertion_points(dmrs_xml)

    # Iterate over tokens and process punctuation tokens
    for punc_token_index, linked_nodes in sorted(punc_token_node_links.items()):

        # Create punctuation node and add it to the DMRS XML
        max_node_id += 1
        node_id = str(max_node_id)

        punc_node = xml.Element('node',
                                attrib={'nodeid': node_id,
                                        'tokalign': str(punc_token_index),
                                        'label': 'punc_%s' % punctuation_dict[tok[punc_token_index]]})
        punc_node.tail = '\n'

        xml.SubElement(punc_node, 'realpred')
        dmrs_xml.insert(node_insert_position, punc_node)
        node_insert_position += 1

        # Connect the punctuation node to all nodes that the punctuation token was previously attached

        for to_node_id in sorted(linked_nodes):
            # Create the link between the new punctuation node and the destination node and add it to the end of DMRS XML
            punc_edge = xml.Element('link',
                                    attrib={'from': node_id,
                                            'to': to_node_id,
                                            'label': 'PUNC_P'})
            punc_edge.tail = '\n'
            sub_node_1 = xml.Element('rargname')
            sub_node_1.text = 'PUNC'
            sub_node_2 = xml.Element('post')
            sub_node_2.text = 'P'
            punc_edge.append(sub_node_1)
            punc_edge.append(sub_node_2)
            dmrs_xml.append(punc_edge)

    return dmrs_xml


def insertion_points(dmrs_xml):
    max_node_id = 0
    node_insert_position = 0

    # Iterate over DMRS nodes to get insertion points and ids
    for entity in dmrs_xml:

        if entity.tag == 'node':
            node = entity
            node_id = node.attrib['nodeid']

            # Keep track of the maximum id for insertion of punctuation nodes and links
            if int(node_id) > max_node_id:
                max_node_id = int(node_id)

            node_insert_position += 1

    return max_node_id, node_insert_position


def punc_to_node_link(dmrs_xml, tok_list, punctuation_dict):

    # Find unaligned tokens and current alignment information
    unaligned_tokens, toks_to_nodes = get_unaligned_tokens(dmrs_xml, len(tok_list))

    for tok_index in unaligned_tokens:
        token = tok_list[tok_index]

        if token not in punctuation_dict:
            continue

    # Not finished implementing


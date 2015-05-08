from collections import defaultdict

from utility import pairwise, contains_sublist
from unaligned_tokens_heuristics import HEURISTIC_DICT


def align(dmrs_xml, tok_list, debug=False):
    '''
    Align currently unaligned tokens to DMRS nodes based on heuristic rules.
    :param dmrs_xml: Input DMRS XML
    :param tok_list: Input token list
    :param debug: Print out intermediary information
    :return: Modified DMRS XML with all tokens aligned (NOTE: if a heuristic can't align a token it will remain unaligned)
    '''

    if debug:
        print tok_list

    # Find unaligned tokens and current alignment information
    unaligned_tokens, toks_to_nodes = get_unaligned_tokens(dmrs_xml, len(tok_list))

    # Attempt to align each pair of unaligned tokens
    tok_to_node_alignment = dict()
    node_to_tok_alignment = defaultdict(list)

    for untoken_index_1, untoken_index_2 in pairwise(unaligned_tokens):

        if untoken_index_1 + 1 != untoken_index_2:
            continue

        untoken_index_range = (untoken_index_1, untoken_index_2)

        node_index = align_unaligned_token(untoken_index_range, tok_list, toks_to_nodes)

        if node_index is not None:
            tok_to_node_alignment[untoken_index_1] = node_index
            tok_to_node_alignment[untoken_index_2] = node_index
            node_to_tok_alignment[node_index].extend([untoken_index_1, untoken_index_2])

    # Attempt to align each remaining unaligned token
    for untoken_index in unaligned_tokens:

        if untoken_index in tok_to_node_alignment:
            continue

        untoken_index_range = (untoken_index, untoken_index)

        node_index = align_unaligned_token(untoken_index_range, tok_list, toks_to_nodes)

        if node_index is not None:
            tok_to_node_alignment[untoken_index] = node_index
            node_to_tok_alignment[node_index].append(untoken_index)

    if debug:
        tmp = [entity for entity in dmrs_xml if entity.tag == 'node']

        for untoken_index in unaligned_tokens:
            untoken_print_out(tok_list[untoken_index], untoken_index, tok_to_node_alignment, tmp)
        print

    # Modify the node alignments in XML with the newly aligned tokens
    node_index = 0
    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        if node_index in node_to_tok_alignment:
            unaligned_toks = node_to_tok_alignment[node_index]
            toks = [int(x) for x in entity.attrib['tokalign'].split(' ') if int(x) != -1]
            new_toks = sorted(toks + unaligned_toks)
            tok_string = ' '.join(str(index) for index in new_toks)
            entity.attrib['tokalign'] = tok_string

        node_index += 1

    return dmrs_xml


def align_unaligned_token(untoken_index_range, tok_list, toks_to_nodes):
    '''
    Align a range of tokens to a DMRS node.
    :param untoken_index_range: Index of starting and ending unaligned token
    :param tok_list: Input token list
    :param toks_to_nodes: Existing token-node alignments information
    :return: The index of the node to align to, or None in case no node to align to could be found
    '''

    untoken = ' '.join(tok_list[index].lower() for index in range(untoken_index_range[0], untoken_index_range[1] + 1))

    if untoken not in HEURISTIC_DICT:
        return None

    funcs = HEURISTIC_DICT[untoken]
    for func, params in funcs:
        node_index = func(untoken_index_range, tok_list, toks_to_nodes, **params)
        if node_index is not None:
            return node_index

    return None


def untoken_print_out(untoken, untoken_index, alignments, tmp):

    if untoken in '.,?!':
        return

    elif untoken_index not in alignments:
        print untoken, 'UNCONNECTED'

    else:
        node = tmp[alignments[untoken_index]]
        node_info = list()

        for subnode in node:
            if subnode.tag == 'realpred':
                node_info = ['', subnode.attrib.get('lemma'), subnode.attrib.get('pos'), subnode.attrib.get('sense'),
                             'rel']
            elif subnode.tag == 'gpred':
                node_info = ['gpred', subnode.text]

        node_str = '_'.join(x for x in node_info if x is not None)

        print untoken, node_str, alignments[untoken_index]


def get_unaligned_tokens(dmrs_xml, num_tokens):
    '''
    Find all tokens we consider unaligned, that is all tokens that do not directly correspond to an 'elementary' node
    in DMRS.

    :param dmrs_xml: XML representation of input DMRS
    :param num_tokens: Number of tokens in the input sentence
    :return (unaligned_tokens, toks_to_nodes): A list of unaligned tokens' indexes and a mapping of token indexes to their
    aligned node information, a tuple of (node_index, node_xml, a list of argument node xmls)
    '''

    aligned_tokens = list()
    toks_to_nodes = defaultdict(list)

    # Create a mapping of node ids to a list of argument nodes
    node_args = get_node_arguments(dmrs_xml)

    # Create aligned_tokens, a list of lists of tokens aligned to each node
    # Create toks_to_nodes, a dictionary of token indexes to node XML entities (1 token can be connected to multiple nodes)
    node_index = 0

    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        tok_indexes = [int(x) for x in entity.attrib['tokalign'].split(' ') if int(x) >= 0]
        if len(tok_indexes) > 0:
            aligned_tokens.append(tok_indexes)

        for tok_index in tok_indexes:
            toks_to_nodes[tok_index].append((node_index, entity, node_args[entity.attrib['nodeid']]))

        node_index += 1

    # Determine the list of unaligned tokens by subtracting sublists of aligned tokens from the list of all tokens
    # Sorting the lists in aligned_tokens by length gives priority to short sublists, which prevents a long span of
    # a general predicate node from making all nodes within it aligned, even though we would not consider them to be aligned.

    aligned_tokens = sorted(aligned_tokens, key=lambda x: len(x))
    unaligned_tokens = range(0, num_tokens)

    for aligned_token in aligned_tokens:
        # If aligned_token list is a sublist of remaining unaligned_tokens, update unaligned_tokens by removing the sublist
        if contains_sublist(unaligned_tokens, aligned_token):
            unaligned_tokens = sorted(set(unaligned_tokens) - set(aligned_token))

    # The remaining tokens in unaligned_tokens are considered unaligned
    # Update the toks_to_nodes to reflect that
    for untoken_index in unaligned_tokens:
        if untoken_index in toks_to_nodes:
            del toks_to_nodes[untoken_index]

    return unaligned_tokens, toks_to_nodes


def get_node_arguments(dmrs_xml):

    nodes = dict()
    node_args = defaultdict(list)

    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        nodes[entity.attrib['nodeid']] = entity

    for entity in dmrs_xml:
        if entity.tag != 'link':
            continue

        from_node_id = entity.attrib['from']
        to_node_id = entity.attrib['to']
        to_node = nodes[to_node_id]

        rarg = ''
        post = ''
        for link_info in entity:
            if link_info.tag == 'rargname':
                rarg = link_info.text
            elif link_info.tag == 'post':
                post = link_info.text

        link_label = '%s/%s' % (rarg, post)

        node_args[from_node_id].append((link_label, to_node))

    return node_args
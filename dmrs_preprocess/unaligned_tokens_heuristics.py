import itertools
import re


def nearest_right(untoken_index_range, tok_list, toks_to_nodes, **params):

    if params.get('limit'):
        limit = params.get('limit')
        del params['limit']
    else:
        limit = 7

    start = untoken_index_range[1] + 1
    end = min(len(tok_list), start + limit)

    for token_index in range(start, end):
        if token_index not in toks_to_nodes:
            continue

        aligned_nodes = toks_to_nodes[token_index]

        for node_index, node, node_args in aligned_nodes:
            if match_node(node, node_args, **params):
                return node_index

    return None


def nearest_left(untoken_index_range, tok_list, toks_to_nodes, **params):

    if params.get('limit'):
        limit = params.get('limit')
        del params['limit']
    else:
        limit = 7

    end = untoken_index_range[0]
    start = max(0, end - limit)

    for token_index in range(start, end)[::-1]:
        if token_index not in toks_to_nodes:
            continue

        aligned_nodes = toks_to_nodes[token_index]
        for node_index, node, node_args in aligned_nodes:
            if match_node(node, node_args, **params):
                return node_index

    return None


def nearest(untoken_index_range, tok_list, toks_to_nodes, **params):

    if params.get('limit'):
        limit = params.get('limit')
        del params['limit']
    else:
        limit = 5

    end_left = untoken_index_range[0]
    start_left = max(0, end_left - limit)

    start_right = untoken_index_range[1] + 1
    end_right = min(len(tok_list), start_right + limit)

    bidirectional_iterator = itertools.chain(*itertools.izip_longest(range(start_left, end_left)[::-1],
                                                                     range(start_right, end_right)))

    for token_index in bidirectional_iterator:
        if token_index not in toks_to_nodes:
            continue

        aligned_nodes = toks_to_nodes[token_index]
        for node_index, node, node_args in aligned_nodes:
            if match_node(node, node_args, **params):
                return node_index

    return None


def match_node(node, node_args, **params):
    params = dict(params)

    for node_info in node:
        if node_info.tag == 'realpred':

            if params.get('realpred'):
                del params['realpred']

            if params.get('pos') and params.get('pos') == node_info.attrib.get('pos'):
                del params['pos']

            if params.get('pos') and isinstance(params.get('pos'), list) and node_info.attrib.get('pos') in params.get('pos'):
                del params['pos']

            if params.get('lemma') and params.get('lemma') == node_info.attrib.get('lemma'):
                del params['lemma']

            if params.get('sense') and params.get('sense') == node_info.attrib.get('sense'):
                del params['sense']

            if params.get('sense_regex') and node_info.attrib.get('sense') is not None and \
                    params.get('sense_regex').match(node_info.attrib.get('sense')):

                del params['sense_regex']

        if node_info.tag == 'sortinfo':
            if params.get('tense') and params.get('tense') == node_info.attrib.get('tense'):
                del params['tense']

            if params.get('perf') and params.get('perf') == node_info.attrib.get('perf'):
                del params['perf']

            if params.get('prog') and params.get('prog') == node_info.attrib.get('prog'):
                del params['prog']

        if params.get('gpred') and node_info.tag == 'gpred':
            del params['gpred']

            if params.get('gpred_rel') and params.get('gpred_rel') == node_info.text:
                del params['gpred_rel']

            if params.get('gpred_rel') and isinstance(params.get('gpred_rel'), list) and node_info.text in params.get('gpred_rel'):
                del params['gpred_rel']

    if params.get('args_or'):
        if match_arg(params.get('args_or'), node_args):
            del params['args_or']

    if len(params) == 0:
        return True
    else:
        return False


def match_arg(arg_or_list, node_args):
    for link_label, node in node_args:
        for link_label_param, node_params in arg_or_list:
            if link_label == link_label_param and match_node(node, [], **node_params):
                return True

    return False


COPULA_GPRED = (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': ['unspec_mod_rel', 'unspec_manner_rel',
                                                                   'comp_or_superl_rel', 'prednom_state_rel',
                                                                   'loc_nonsp_rel']})

HEURISTIC_DICT = {'do': [(nearest_right, {'realpred': True, 'pos': 'v', 'tense': 'pres'})],
                  'does': [(nearest_right, {'realpred': True, 'pos': 'v', 'tense': 'pres'})],
                  'did': [(nearest_right, {'realpred': True, 'pos': 'v', 'tense': 'past'})],
                  'have': [(nearest_right, {'limit': 5, 'realpred': True, 'pos': 'v', 'tense': 'pres'})],
                  'has': [(nearest_right, {'limit': 5, 'realpred': True, 'pos': 'v', 'tense': 'pres'})],
                  'had': [(nearest_right, {'limit': 5, 'realpred': True, 'pos': 'v', 'tense': 'past'})],
                  'both': [(nearest_right, {'realpred': True, 'lemma': 'and', 'pos': 'c'})],
                  'either': [(nearest_right, {'realpred': True, 'lemma': 'or', 'pos': 'c'})],
                  'neither': [(nearest_right, {'realpred': True, 'lemma': 'nor', 'pos': 'c'})],
                  'not': [(nearest_right, {'realpred': True, 'lemma': 'but', 'pos': 'c'})],
                  'not only': [(nearest_right, {'limit': 15, 'realpred': True, 'lemma': 'but+also', 'pos': 'c'})],
                  'not just': [(nearest_right, {'limit': 15, 'realpred': True, 'lemma': 'but+also', 'pos': 'c'})],
                  'rather': [(nearest_right, {'limit': 15, 'realpred': True, 'lemma': 'rather+than', 'pos': 'c'})],
                  'much rather': [(nearest_right, {'limit': 15, 'realpred': True, 'lemma': 'rather+than', 'pos': 'c'})],
                  'there': [(nearest, {'realpred': True, 'lemma': 'be', 'pos': 'v', 'sense': 'there'})],
                  'will': [(nearest_right, {'realpred': True, 'pos': 'v', 'tense': 'fut'})],
                  'shall': [(nearest_right, {'realpred': True, 'pos': 'v', 'tense': 'fut'})],
                  'is': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres'}),
                         COPULA_GPRED],
                  'are': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres'}),
                          COPULA_GPRED],
                  'am': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres'}),
                         COPULA_GPRED],
                  'were': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'past'}),
                           COPULA_GPRED],
                  'been': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres', 'perf': '+'}),
                           COPULA_GPRED],
                  'has been': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres', 'perf': '+'}),
                               COPULA_GPRED],
                  'have been': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres', 'perf': '+'}),
                                COPULA_GPRED],
                  'had been': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'pres', 'perf': '+'}),
                               COPULA_GPRED],
                  'being': [(nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'prog': '+'}),
                            COPULA_GPRED],
                  'be': [(nearest_left, {'limit': 1, 'realpred': True, 'pos': 'v', 'sense': 'modal'}),
                         (nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p'], 'tense': 'untensed'}),
                         COPULA_GPRED],
                  'who': [(nearest_right, {'realpred': True, 'pos': 'v', 'args_or': [('ARG1/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                     ('ARG2/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                     ('ARG3/EQ', {'realpred': True, 'pos': 'n'})]
                          }),
                          (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': ['subord_rel', 'relative_mod_rel']}),
                          (nearest_right, {'realpred': True, 'lemma': 'be', 'pos': 'v', 'sense': 'itcleft'}),
                          (nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p']}),
                          COPULA_GPRED],
                  'whom': [(nearest_right, {'realpred': True, 'pos': 'v', 'args_or': [('ARG2/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                      ('ARG3/EQ', {'realpred': True, 'pos': 'n'})]
                           }),
                          (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': ['subord_rel', 'relative_mod_rel']}),
                          (nearest_right, {'realpred': True, 'lemma': 'be', 'pos': 'v', 'sense': 'itcleft'}),
                          (nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p']}),
                          COPULA_GPRED],
                  'which': [(nearest_right, {'realpred': True, 'pos': 'v', 'args_or': [('ARG1/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                       ('ARG2/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                       ('ARG3/EQ', {'realpred': True, 'pos': 'n'})]
                           }),
                          (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': ['subord_rel', 'relative_mod_rel']}),
                          (nearest_right, {'realpred': True, 'lemma': 'be', 'pos': 'v', 'sense': 'itcleft'}),
                          (nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p']}),
                          COPULA_GPRED],
                  'that': [(nearest_left, {'realpred': True, 'pos': 'v', 'args_or': [('ARG2/H', {}), ('ARG3/EH', {})]}),
                           (nearest_right, {'realpred': True, 'pos': 'v', 'args_or': [('ARG1/H', {})]}),
                           (nearest_right, {'realpred': True, 'pos': 'v', 'args_or': [('ARG1/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                      ('ARG2/EQ', {'realpred': True, 'pos': 'n'}),
                                                                                      ('ARG3/EQ', {'realpred': True, 'pos': 'n'})]
                           }),
                          (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': ['subord_rel', 'relative_mod_rel', 'comp_so_rel']}),
                          (nearest_right, {'realpred': True, 'lemma': 'be', 'pos': 'v', 'sense': 'itcleft'}),
                          (nearest_right, {'realpred': True, 'pos': ['v', 'a', 'p']}),
                          COPULA_GPRED],
                  'and': [(nearest, {'limit': 3, 'gpred': True, 'gpred_rel': ['times_rel', 'fraction_rel']}),
                          (nearest_left, {'realpred': True, 'lemma': 'try', 'pos': 'v', 'sense': '1'})],
                  'but': [(nearest_left, {'realpred': True, 'lemma': 'help', 'pos': 'v', 'sense': 'but'})],
                  'to': [(nearest_right, {'realpred': True, 'pos': 'v', 'tense': 'untensed'}),
                         (nearest_right, {'realpred': True, 'lemma': 'for', 'pos': 'x', 'sense': 'cond'}),
                         (nearest_right, {'realpred': True, 'lemma': 'in+order+to', 'pos': 'x'}),
                         (nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?to(-[^_]+)?')})],
                  'as': [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?as(-[^_]+)?')}),
                         (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': 'comp_equal_rel'})],
                  'as to': [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?as\+to(-[^_]+)?')})],
                  'by': [(nearest, {'limit': 3, 'realpred': True, 'sense': 'by'}),
                         (nearest_left, {'realpred': True, 'pos': 'v'})],
                  'of': [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?of(-[^_]+)?')}),
                         (nearest, {'limit': 5, 'gpred': True, 'gpred_rel': ['part_of_rel', 'day_rel', 'mofy_rel',
                                                                             'place_n_rel', 'day_part_rel', 'def_day_part_rel',
                                                                             'nominalization_rel', 'generic_entity_rel']}),
                         (nearest, {'limit': 3, 'realpred': True, 'sense': 'ofj'})],
                  'out of': [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?out\+of(-[^_]+)?')})],
                  'round': [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?around(-[^_]+)?')})],
                  'upside down': [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?upside\+down(-[^_]+)?')})],
                  }

SENSE_LIST = ['aback', 'across', 'after', 'against', 'ahead', 'along', 'among', 'apart', 'around', 'aside',
              'at', 'away', 'back', 'behind', 'between', 'down', 'even', 'for', 'forth', 'forward', 'from',
              'go', 'in', 'into', 'off', 'on', 'onto', 'onward', 'onwards', 'open', 'out', 'over', 'short',
              'so', 'still', 'home', 'thin', 'through', 'than', 'together', 'toward', 'towards', 'under',
              'until', 'up', 'upon', 'with', 'without', 'yet']

SENSE_DICT = dict((string, [(nearest, {'limit': 3, 'realpred': True, 'sense_regex': re.compile('-?%s(-[^_]+)?' % string)})]) for string in SENSE_LIST)
HEURISTIC_DICT.update(SENSE_DICT)

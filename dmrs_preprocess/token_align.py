from collections import defaultdict
import Levenshtein

from utility import pairwise


LEVENSHTEIN_RATIO = 0.90


def align(dmrs_xml, untok, tok):
    '''
    Align tokens to DMRS nodes based on untokenized character strings.
    :param dmrs_xml: Input DMRS XML
    :param untok: Input untokenized sentence string
    :param tok: Input list of tokens
    :return: DMRS XML aligned to tokens.
    '''

    # Determine the untokenized strings that character spans correspond to
    # char_spans: dictionary of character spans and their associated untokenized strings
    char_spans = get_node_strings(dmrs_xml, untok)

    # Somewhat fuzzy matching of the elementary character spans to tokens
    # match_dict: dictionary of character spans and their associated token indexes
    match_dict = match_basic_tokens(char_spans, tok)
    match_compound_tokens(char_spans, match_dict)

    # Attach token alignment information to nodes
    dmrs_token_aligned = attach_token_info(dmrs_xml, match_dict)

    return dmrs_token_aligned


def get_node_strings(dmrs_xml, untok):

    char_spans = defaultdict(list)

    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        start, end = int(entity.attrib['cfrom']), int(entity.attrib['cto'])

        char_spans[start].append((end, untok[start:end+1]))

    char_spans_sorted = dict()
    for start, span_list in char_spans.items():
        char_spans_sorted[start] = sorted(span_list)

    return char_spans_sorted


def match_basic_tokens(char_spans, tok_list):

    tok_pointer = 0
    match_dict = dict()

    for start in sorted(char_spans.keys()):
        end, untok_string = char_spans[start][0]
        untok_string = untok_string.strip()

        found = False
        for tok_index, tok in enumerate(tok_list[tok_pointer:]):

            if match_token(untok_string, tok):
                match_dict[(start, end)] = [tok_pointer + tok_index]
                tok_pointer += tok_index + 1
                found = True
                break

        if found:
            continue

        tok_index = tok_pointer
        for tok1, tok2 in pairwise(tok_list[tok_pointer:]):

            if match_2token(untok_string, tok1, tok2):
                match_dict[(start, end)] = [tok_index, tok_index + 1]
                tok_pointer = tok_index + 2
                break

            tok_index += 1

    return match_dict


def match_compound_tokens(char_spans, match_dict):

    for start in sorted(char_spans.keys()):
        for end, untok_string in char_spans[start]:

            span = (start, end)

            # If span is already in match_dict, problem is already solved, skip
            if span in match_dict:
                continue

            # Determine the elementary starting token span
            start_token_end, _ = char_spans[start][0]
            start_token_span = (start, start_token_end)

            # If elementary token is not in match_dict, skip
            if start_token_span not in match_dict:
                continue

            # Determine the elementary ending token span
            end_token_span = find_end(end, char_spans)

            # If it is not in match_dict, skip
            if end_token_span is None or end_token_span not in match_dict:
                continue

            # Grab the first matched token of starting elementary token
            # and the last matched token of ending elementary token
            start_token = match_dict[start_token_span][0]
            end_token = match_dict[end_token_span][-1]

            match_dict[span] = range(start_token, end_token + 1)


def attach_token_info(dmrs_xml, match_dict):
    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        span = int(entity.attrib['cfrom']), int(entity.attrib['cto'])

        if span in match_dict:
            toks = match_dict[span]
            tok_string = ' '.join(str(index) for index in toks)
        else:
            tok_string = '-1'

        entity.attrib['tokalign'] = tok_string

    return dmrs_xml


def match_token(untok_string, tok_string):
    untok_string = untok_string.strip()
    untok_nopunc = untok_string.rstrip('\'\"-,.:;!?')

    if untok_string == tok_string or untok_string.lower() == tok_string:
        return True

    if untok_nopunc == tok_string or untok_nopunc.lower() == tok_string:
        return True

    if Levenshtein.ratio(untok_string, tok_string) > LEVENSHTEIN_RATIO:
        return True

    return False


def match_2token(untok_string, tok1, tok2):
    return match_token(untok_string, tok1 + ' ' + tok2) or \
            match_token(untok_string, tok1 + tok2)


def find_end(target_end, char_spans):
    for start in sorted(char_spans.keys()):
        if start >= target_end:
            break

        end, _ = char_spans[start][0]
        if target_end == end:
            return start, end

    return None



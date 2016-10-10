

def handle_unknown_nodes(dmrs_xml, lemmatizer):
    """
    Convert unknown nodes' lemma and pos tags (presented as lemma="jumped/VBD") into standard form (lemma="jump",pos="v").
    :param dmrs_xml: DMRS XML object
    :param lemmatizer: Initialized Spacy lemmatizer object
    :return: Modified DMRS XML object
    """

    for entity in dmrs_xml:

        if entity.tag != 'node':
            continue

        pred = entity.find('./realpred')

        if pred is None or not pred.attrib.get('pos') == 'u':
            continue

        old_pos = pred.attrib.get('lemma').replace('//', '/').split('/')[-1]
        new_pos = convert_pos(old_pos)

        old_lemma = '/'.join(pred.attrib.get('lemma').replace('//', '/').split('/')[:-1])

        if new_pos == 'n':
            new_lemma = lemmatizer.noun(old_lemma).pop()

        elif new_pos == 'a':
            new_lemma = lemmatizer.adj(old_lemma).pop()

        elif new_pos == 'v':
            new_lemma = lemmatizer.verb(old_lemma).pop()

        else:
            new_lemma = old_lemma

        pred.attrib['lemma'] = new_lemma
        pred.attrib['pos'] = new_pos
        del pred.attrib['sense']

    return dmrs_xml


def convert_pos(pos_tag):

    if pos_tag[0] == 'N' or pos_tag == 'FW':
        return 'n'

    elif pos_tag[0] == 'J' or pos_tag == 'RB':
        return 'a'

    elif pos_tag[0] == 'V':
        return 'v'

    else:
        return 'u'

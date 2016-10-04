

def map_tokens(dmrs_xml, tok, wmap):
    idx = [wmap[token.lower()] for token in tok]

    for entity in dmrs_xml:
        if entity.tag != 'node':
            continue

        tokalign = entity.attrib.get('tokalign')

        if tokalign is None or tokalign == '-1':
            continue

        tokalign = [int(x) for x in tokalign.split()]
        node_tok = [tok[index] for index in tokalign]
        node_idx = [idx[index] for index in tokalign]

        entity.attrib['tok'] = ' '.join(node_tok)
        entity.attrib['tok_idx'] = ' '.join(str(x) for x in node_idx)

    return dmrs_xml


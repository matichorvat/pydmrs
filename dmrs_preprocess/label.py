

def create_label(dmrs_xml, carg_clean=False):
    '''
    Create an identifying label attribute for each node and link,
    consisting of its arguments and properties.
    :param dmrs_xml: Input DMRS XML
    :return: Modified DMRS XML
    '''

    for entity in dmrs_xml:
        if entity.tag == 'node':

            node_attribs = dict()
            # Remove quotes around CARG
            if entity.attrib.get('carg') is not None:
                if carg_clean:
                    entity.attrib['carg'] = entity.attrib['carg'][1:-1]

                node_attribs['carg'] = entity.attrib['carg']

            # Collect node attributes in a dictionary
            for node_info in entity:
                node_attribs.update(node_info.attrib)

                if node_info.tag == 'gpred':
                    node_attribs[node_info.tag] = node_info.text

            # Construct the label attribute
            tense = node_attribs.get('tense') if node_attribs.get('tense') is not None and node_attribs.get('tense').lower() != 'untensed' else None
            sf = node_attribs.get('sf') if node_attribs.get('sf') != 'prop' else None

            attribs_of_interest = [node_attribs.get('carg'), node_attribs.get('gpred'),
                                   node_attribs.get('lemma'), node_attribs.get('pos'),
                                   node_attribs.get('sense'), node_attribs.get('pers'),
                                   node_attribs.get('num'), tense,
                                   node_attribs.get('gend'), sf]

            label = '_'.join([unicode(x) for x in attribs_of_interest if x is not None])

            if node_attribs.get('gpred') is None:
                label = '_' + label

            # Attach the label to node XML
            entity.attrib['label'] = label

        elif entity.tag == 'link':
            # Get ARG and POST of a link
            arg = entity.findall('rargname')[0].text if entity.findall('rargname') else None
            post = entity.findall('post')[0].text if entity.findall('post') else None

            # Create a label and attach it to the link XML
            entity.attrib['label'] = '_'.join([x for x in [arg, post] if x is not None])

    return dmrs_xml

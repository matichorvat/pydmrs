
def handle_ltop_links(dmrs_xml):
    '''
    Remove LTOP links from DMRS and add LTOP attribute to the DMRS entity
    :param dmrs_xml: Input DMRS XML
    :return: Modified DMRS XML
    '''

    ltop = '-1'
    links_to_remove = list()
    for entity in dmrs_xml:

        if entity.tag == 'link':
            link = entity

            # Remove LTOP (ghost) link
            if link.attrib['from'] == '0':
                links_to_remove.append(link)
                ltop = link.attrib['to']

    for link in links_to_remove:
        dmrs_xml.remove(link)

    dmrs_xml.attrib['ltop'] = ltop

    if 'index' not in dmrs_xml.attrib:
        dmrs_xml.attrib['index'] = '-1'

    return dmrs_xml

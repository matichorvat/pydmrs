
def remove_ltop_links(dmrs_xml):
    '''
    Remove LTOP links from DMRS
    :param dmrs_xml: Input DMRS XML
    :return: Modified DMRS XML
    '''

    links_to_remove = list()
    for entity in dmrs_xml:

        if entity.tag == 'link':
            link = entity

            # Remove LTOP (ghost) link
            if link.attrib['from'] == '0':
                links_to_remove.append(link)

    for link in links_to_remove:
        dmrs_xml.remove(link)

    return dmrs_xml
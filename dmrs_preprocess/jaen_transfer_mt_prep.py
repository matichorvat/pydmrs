import xml.etree.ElementTree as xml

from label import collect_node_attribs


gpred_map = {
    'discourse_x': 'discourse',
    'ellipses': 'ellipsis',
    'if_then': 'if_x_then',
    'neg_x': 'neg',
    'number': 'number_q',
    'part-of': 'part_of',
    'unknown_v': 'unknown',
    'unknown_v_cop': 'cop_id',
    'unspec_p_manner': 'unspec_manner'
}


def preprocess(dmrs_xml):

    for index, entity in enumerate(dmrs_xml):
        if entity.tag == 'node':

            node_attribs = collect_node_attribs(entity)

            if node_attribs.get('num') == 'number':
                augment_child_attribute(entity, 'sortinfo', 'num', 'sg')
                node_attribs['num'] = 'sg'

            if node_attribs.get('sf') == 'sforce':
                augment_child_attribute(entity, 'sortinfo', 'sf', 'prop')
                node_attribs['num'] = 'prop'

            if node_attribs.get('pers') == 'person':
                augment_child_attribute(entity, 'sortinfo', 'pers', '3')
                node_attribs['pers'] = '3'

            if node_attribs.get('sense') == '0':
                augment_child_attribute(entity, 'realpred', 'sense', '1')
                node_attribs['sense'] = '1'

            if node_attribs.get('perf') == 'luk' or (node_attribs.get('pos') == 'v' and node_attribs.get('perf') is None):
                augment_child_attribute(entity, 'sortinfo', 'perf', '-')
                node_attribs['perf'] = '-'

            if node_attribs.get('prog') == 'luk' or (node_attribs.get('pos') == 'v' and node_attribs.get('prog') is None):
                augment_child_attribute(entity, 'sortinfo', 'prog', '-')
                node_attribs['prog'] = '-'

            if node_attribs.get('gpred') is not None:

                # Remove '_rel' at the end of gpreds
                if node_attribs.get('gpred').endswith('_rel'):
                    gpred_text = '_'.join(node_attribs.get('gpred').split('_')[:-1])
                    augment_child_attribute(entity, 'gpred', 'text', gpred_text)
                    node_attribs['gpred'] = gpred_text

                # Make ja realpred
                if node_attribs.get('gpred').startswith('ja:_'):
                    ja_pred = node_attribs.get('gpred')[4:]
                    ja_pred_split = ja_pred.split('_')

                    ja_lemma = ja_pred_split[0]
                    ja_pos = ja_pred_split[1]
                    realpred_attrib = {'lemma': '_ja_' + ja_lemma, 'pos': ja_pos}

                    if len(ja_pred_split) > 2:
                        ja_sense = ja_pred_split[2]
                        realpred_attrib['sense'] = ja_sense

                    node_xml = create_realpred_replacement_node(
                        entity,
                        realpred_attrib=realpred_attrib,
                        carg=ja_lemma
                    )
                    dmrs_xml[index] = node_xml
                    del node_attribs['gpred']

                # Make ja gpred
                elif node_attribs.get('gpred').startswith('ja:'):
                    ja_gpred = node_attribs.get('gpred')[3:]
                    augment_child_attribute(entity, 'gpred', 'text', ja_gpred)
                    node_attribs['gpred'] = ja_gpred

                # Change gpred nodes
                if node_attribs.get('gpred') == 'def_udef_a_q' or node_attribs.get('gpred') == 'def_q':
                    node_xml = create_realpred_replacement_node(entity, realpred_attrib={'lemma': 'the', 'pos': 'q'})
                    dmrs_xml[index] = node_xml

                elif node_attribs.get('gpred') == 'pron' and node_attribs.get('pers') == '2' and node_attribs.get('gend') is not None:
                    augment_child_attribute(entity, 'sortinfo', 'gend')
                    del node_attribs['gend']

                elif node_attribs.get('gpred') == 'pron' and node_attribs.get('pers') == '3' and node_attribs.get('num') is None:
                    augment_child_attribute(entity, 'sortinfo', 'num', 'pl')  # pron_3 -> pron_3_pl (they)
                    node_attribs['num'] = 'pl'

                elif node_attribs.get('gpred') in gpred_map:
                    gpred_text = gpred_map[node_attribs.get('gpred')]
                    augment_child_attribute(entity, 'gpred', 'text', gpred_text)
                    node_attribs['gpred'] = gpred_text

    return dmrs_xml


def augment_child_attribute(xml_element, child_tag, attribute_name, replacement=None):
    for child in xml_element:
        if child.tag == child_tag:
            if attribute_name == 'text':
                child.text = replacement
            elif replacement is not None:
                child.attrib[attribute_name] = replacement
            else:
                del child.attrib[attribute_name]

            break


def create_realpred_replacement_node(old_node_xml, realpred_attrib=None, sortinfo_attrib=None, carg=None):
    node = create_xml_node(old_node_xml)

    if carg is not None:
        node.attrib['carg'] = u'"{}"'.format(carg)

    realpred = xml.Element('realpred')
    sortinfo = xml.Element('sortinfo')
    node.append(realpred)
    node.append(sortinfo)

    if realpred_attrib is not None:
        realpred.attrib = realpred_attrib

    if sortinfo_attrib is not None:
        sortinfo.attrib = sortinfo_attrib

    return node


def create_gpred_replacement_node(old_node_xml, gpred_text, carg=None):
    node = create_xml_node(old_node_xml)

    if carg is not None:
        node.attrib['carg'] = u'"{}"'.format(carg)

    gpred = xml.Element('gpred')
    gpred.text = gpred_text
    node.append(gpred)

    return node


def create_xml_node(old_node_xml):
    node = xml.Element(
        'node',
        attrib={
            'nodeid': old_node_xml.attrib.get('nodeid'),
            'cfrom': old_node_xml.attrib.get('cfrom'),
            'cto': old_node_xml.attrib.get('cto'),
        }
    )
    node.tail = '\n'
    return node

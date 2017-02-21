#!/usr/bin/env python

import os
import errno
import sys
import argparse
import xml.etree.ElementTree as xml
from xml.etree.ElementTree import ParseError

import token_align
import unaligned_tokens_align
import label
import filter_gpred
import handle_ltop
import handle_unknown
import cycle_remove
import map_tokens
import jaen_transfer_mt_prep
from utility import empty, load_wmap, strip_source_information


def split_dmrs_file(content):
    content_split = content.split('<dmrs')
    content_filter = filter(lambda x: x.strip() != '', content_split)
    content_fixed = [('<dmrs' + x).strip() for x in content_filter]
    return content_fixed


def read_file(filename, format='dmrs'):
    with open(filename, 'rb') as f:
        content = f.read().decode('utf-8').strip()

        if format == 'dmrs':
            return split_dmrs_file(content)
        elif format == 'untok':
            return [sent.strip() for sent in content.split('\n')]
        elif format == 'tok':
            return [sent.strip().split(' ') for sent in content.split('\n')]
        else:
            raise NotImplementedError('Format %s not supported.' % format)


def write_file(filename, dmrs_list):
    with open(filename, 'wb') as f:
        f.write('\n\n'.join(dmrs_list))


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            sys.stderr.write("Error creating directory: %s" % path)
            raise


def process(dmrs, untok, tok,
            token_align_opt=False,
            unaligned_align_opt=False,
            label_opt=False,
            handle_ltop_opt=False,
            gpred_filter=None,
            gpred_curb_opt=None,
            cycle_remove_opt=False,
            map_node_tokens=None,
            attach_untok=False,
            attach_tok=False,
            unknown_handle_lemmatizer=None,
            realization=False,
            realization_sanity_check=False,
            transfer_mt_prep=False):

    parser = xml.XMLParser(encoding='utf-8')

    try:
        dmrs_xml = xml.fromstring(dmrs.encode('utf-8'), parser=parser)

    except ParseError:
        sys.stderr.write(dmrs + "\n")
        raise

    if empty(dmrs_xml):
        return dmrs

    if transfer_mt_prep:
        dmrs_xml = jaen_transfer_mt_prep.preprocess(dmrs_xml)

    if handle_ltop_opt:
        dmrs_xml = handle_ltop.handle_ltop_links(dmrs_xml)

    if gpred_filter is not None:
        dmrs_xml = filter_gpred.filter_gpred(dmrs_xml, gpred_filter, handle_ltop=handle_ltop_opt)

    if token_align_opt and not realization_sanity_check and not transfer_mt_prep:
        dmrs_xml = token_align.align(dmrs_xml, untok, tok)

    if unaligned_align_opt and not realization_sanity_check and not transfer_mt_prep:
        if not token_align_opt:
            sys.stderr.write('Warning: Token alignment needed before attempting to align unaligned tokens.')

        dmrs_xml = unaligned_tokens_align.align(dmrs_xml, tok)

    if gpred_curb_opt and not realization_sanity_check and not transfer_mt_prep:
        dmrs_xml = filter_gpred.curb_gpred_spans(dmrs_xml)

    if unknown_handle_lemmatizer is not None:
        dmrs_xml = handle_unknown.handle_unknown_nodes(dmrs_xml, unknown_handle_lemmatizer)

    if label_opt:
        dmrs_xml = label.create_label(dmrs_xml, carg_clean=True)

    if cycle_remove_opt:
        dmrs_xml = cycle_remove.cycle_remove(dmrs_xml, realization=realization)

    if map_node_tokens is not None and not realization_sanity_check and not transfer_mt_prep:
        wmap = map_node_tokens
        dmrs_xml = map_tokens.map_tokens(dmrs_xml, tok, wmap)

    if attach_untok and not realization_sanity_check and not transfer_mt_prep:
        dmrs_xml.attrib['untok'] = untok

    if attach_tok and not realization_sanity_check and not transfer_mt_prep:
        dmrs_xml.attrib['tok'] = ' '.join(tok)

    if realization_sanity_check:
        dmrs_xml = strip_source_information(dmrs_xml)

    dmrs_string = xml.tostring(dmrs_xml, encoding='utf-8')

    return dmrs_string


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='DMRS preprocessing tool.')
    parser.add_argument('-t', '--token_align', action='store_true',
                        help='Align tokens to nodes.')
    parser.add_argument('-u', '--unaligned_align', action='store_true',
                        help='Align unaligned tokens to nodes using heuristic rules.')
    parser.add_argument('-l', '--label', action='store_true',
                        help='Create label attribute for nodes and links.')
    parser.add_argument('-r', '--handle_ltop', action='store_true',
                        help='Remove LTOP link originating from non-existing node with id 0 and add it as an attribute.')
    parser.add_argument('--handle_unknown', action='store_true',
                        help='Handle unknown words (e.g. jumped/VBD).')
    parser.add_argument('-f', '--filter_gpred', default=None,
                        help='Filter out unneeded general predicate nodes and links. Specify filename with the filter.')
    parser.add_argument('-g', '--gpred_curb', default=None, type=int,
                        help='Curb the spans of general predicate nodes to the specified number of tokens. If exceeded, the alignment for the node is removed.')
    parser.add_argument('--cycle_remove', action='store_true',
                        help='Remove cycles in the DMRS graph.')
    parser.add_argument('-m', '--map_node_tokens', default=None,
                        help='Add tokens and token idx to nodes. Requires a word map file to be specified.')
    parser.add_argument('--realization', action='store_true',
                        help='Turn on realization mode which does not use tokalign information in graph cycle removal.')
    parser.add_argument('--realization_sanity_check', action='store_true',
                        help='Turn on sanity check mode for realization which strips all source sentence information from DMRS graphs.')
    parser.add_argument('--transfer_mt_prep', action='store_true',
                        help='Preprocess DMRS obtained from transfer MT system.')
    parser.add_argument('-au', '--attach_untok', action='store_true', help='Attach the untokenized sentence to DMRS.')
    parser.add_argument('-at', '--attach_tok', action='store_true', help='Attach the tokenized sentence to DMRS.')
    parser.add_argument('input_dmrs', help='Specify input dmrs file')
    parser.add_argument('input_untok', help='Specify input untokenized file')
    parser.add_argument('input_tok', help='Specify input tokenized file')
    parser.add_argument('output_dmrs', help='Specify output dmrs file. Set "-" to output to standard output.')

    args = parser.parse_args()

    dmrs_list = read_file(args.input_dmrs, format='dmrs')

    if not args.transfer_mt_prep:
        untok_list = read_file(args.input_untok, format='untok')
        tok_list = read_file(args.input_tok, format='tok')
    else:
        untok_list = [''] * len(dmrs_list)
        tok_list = [''] * len(dmrs_list)

    if args.filter_gpred is not None:
        gpred_filter = filter_gpred.parse_gpred_filter_file(args.filter_gpred)
    else:
        gpred_filter = None

    if args.handle_unknown:
        import spacy
        lemmatizer = spacy.lemmatizer.Lemmatizer.from_package(spacy.util.get_package_by_name('en'))

    else:
        lemmatizer = None

    if args.map_node_tokens is not None:
        wmap = load_wmap(args.map_node_tokens)
    else:
        wmap = None

    if args.output_dmrs == '-':
        out = sys.stdout
    else:
        out = open(args.output_dmrs, 'wb')

    dmrs_processed_list = list()
    for dmrs, untok, tok in zip(dmrs_list, untok_list, tok_list):

        dmrs_processed = process(dmrs, untok, tok,
                                 token_align_opt=args.token_align,
                                 unaligned_align_opt=args.unaligned_align,
                                 label_opt=args.label,
                                 handle_ltop_opt=args.handle_ltop,
                                 gpred_filter=gpred_filter,
                                 unknown_handle_lemmatizer=lemmatizer,
                                 cycle_remove_opt=args.cycle_remove,
                                 gpred_curb_opt=args.gpred_curb,
                                 map_node_tokens=wmap,
                                 attach_untok=args.attach_untok,
                                 attach_tok=args.attach_tok,
                                 realization=args.realization,
                                 realization_sanity_check=args.realization_sanity_check,
                                 transfer_mt_prep=args.transfer_mt_prep)

        out.write('%s\n\n' % dmrs_processed)

    if args.output_dmrs != '-':
        out.close()

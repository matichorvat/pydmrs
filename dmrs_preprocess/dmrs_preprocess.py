#!/usr/bin/python

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
from utility import empty


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
            punc_opt=False,
            label_opt=False,
            handle_ltop_opt=False,
            gpred_filter=None,
            gpred_curb_opt=None,
            cycle_remove_opt=False,
            attach_untok=False,
            attach_tok=False,
            unknown_handle_lemmatizer=None):

    parser = xml.XMLParser(encoding='utf-8')

    try:
        dmrs_xml = xml.fromstring(dmrs.encode('utf-8'), parser=parser)

    except ParseError:
        sys.stderr.write(dmrs + "\n")
        raise

    if empty(dmrs_xml):
        return dmrs

    if handle_ltop_opt:
        dmrs_xml = handle_ltop.handle_ltop_links(dmrs_xml)

    if gpred_filter is not None:
        dmrs_xml = filter_gpred.filter_gpred(dmrs_xml, gpred_filter, handle_ltop=handle_ltop_opt)

    if token_align_opt:
        dmrs_xml = token_align.align(dmrs_xml, untok, tok)

    if unaligned_align_opt:
        if not token_align_opt:
            sys.stderr.write('Warning: Token alignment needed before attempting to align unaligned tokens.')

        dmrs_xml = unaligned_tokens_align.align(dmrs_xml, tok)

    if gpred_curb_opt:
        dmrs_xml = filter_gpred.curb_gpred_spans(dmrs_xml)

    if punc_opt:
        pass

    if unknown_handle_lemmatizer is not None:
        dmrs_xml = handle_unknown.handle_unknown_nodes(dmrs_xml, unknown_handle_lemmatizer)

    if label_opt:
        dmrs_xml = label.create_label(dmrs_xml, carg_clean=True)

    if cycle_remove_opt:
        dmrs_xml = cycle_remove.cycle_remove(dmrs_xml)

    if attach_untok:
        dmrs_xml.attrib['untok'] = untok

    if attach_tok:
        dmrs_xml.attrib['tok'] = ' '.join(tok)

    dmrs_string = xml.tostring(dmrs_xml, encoding='utf-8')

    return dmrs_string


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='DMRS preprocessing tool.')
    parser.add_argument('-t', '--token_align', action='store_true',
                        help='Align tokens to nodes.')
    parser.add_argument('-u', '--unaligned_align', action='store_true',
                        help='Align unaligned tokens to nodes using heuristic rules.')
    parser.add_argument('-p', '--punctuation', action='store_true',
                        help='Create punctuation nodes and links, and align them to punctuation tokens.')
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
    parser.add_argument('-g', '--cycle_remove', action='store_true',
                        help='Remove cycles in the DMRS graph.')
    parser.add_argument('-au', '--attach_untok', action='store_true', help='Attach the untokenized sentence to DMRS.')
    parser.add_argument('-at', '--attach_tok', action='store_true', help='Attach the tokenized sentence to DMRS.')
    parser.add_argument('input_dmrs', help='Specify input dmrs file')
    parser.add_argument('input_untok', help='Specify input untokenized file')
    parser.add_argument('input_tok', help='Specify input tokenized file')
    parser.add_argument('output_dmrs', help='Specify output dmrs file. Set "-" to output to standard output.')

    args = parser.parse_args()

    dmrs_list = read_file(args.input_dmrs, format='dmrs')
    untok_list = read_file(args.input_untok, format='untok')
    tok_list = read_file(args.input_tok, format='tok')

    if args.filter_gpred is not None:
        gpred_filter = filter_gpred.parse_gpred_filter_file(args.filter_gpred)
    else:
        gpred_filter = None

    if args.handle_unknown:
        import spacy
        lemmatizer = spacy.lemmatizer.Lemmatizer.from_package(spacy.util.get_package_by_name('en'))

    else:
        lemmatizer = None

    if args.output_dmrs == '-':
        out = sys.stdout
    else:
        out = open(args.output_dmrs, 'wb')

    dmrs_processed_list = list()
    for dmrs, untok, tok in zip(dmrs_list, untok_list, tok_list):
        dmrs_processed = process(dmrs, untok, tok,
                                 token_align_opt=args.token_align,
                                 unaligned_align_opt=args.unaligned_align,
                                 punc_opt=args.punctuation,
                                 label_opt=args.label,
                                 handle_ltop_opt=args.handle_ltop,
                                 gpred_filter=gpred_filter,
                                 unknown_handle_lemmatizer=lemmatizer,
                                 cycle_remove_opt=args.cycle_remove,
                                 gpred_curb_opt=args.gpred_curb,
                                 attach_untok=args.attach_untok,
                                 attach_tok=args.attach_tok)
        
        out.write('%s\n\n' % dmrs_processed)

    if args.output_dmrs != '-':
        out.close()

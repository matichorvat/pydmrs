#!/usr/bin/env python

import os
import sys
import errno
import argparse
from collections import Counter
import xml.etree.ElementTree as xml

from vocab import SourceGraphVocab, SourceGraphCargVocab
from wmap import SourceGraphWMAP


def split_dmrs_file(content):
    content_split = content.split('<dmrs')
    content_filter = filter(lambda x: x.strip() != '', content_split)
    content_fixed = [('<dmrs' + x).strip() for x in content_filter]
    return content_fixed


def empty(dmrs_xml):
    count = 0
    for child in dmrs_xml:
        return False

    return True


def read_file(filename):
    with open(filename, 'rb') as f:
        content = f.read().decode('utf-8').strip()
        return split_dmrs_file(content)


def vocab_extract_stdin(vocab):

    dmrs = ''

    while True:
        try:
            dmrs_line = raw_input().decode('utf-8').strip()

            if dmrs_line.startswith('<dmrs'):
                dmrs = dmrs_line

            elif dmrs_line.startswith('</dmrs>'):
                dmrs += dmrs_line

                parser = xml.XMLParser(encoding='utf-8')
                dmrs_xml = xml.fromstring(dmrs.encode('utf-8'), parser=parser)
                vocab.extract_sentence(dmrs_xml)

            else:
                dmrs += dmrs_line

        except EOFError:
            break


def create_wmap(vocab_filename, existing_wmap=None):

    vocab = Counter()

    with open(vocab_filename) as f:
        content = f.read().decode('utf-8').strip()

        for line in content.split('\n'):
            line_split = line.strip().split('\t')

            try:
                vocab[line_split[0]] += int(line_split[1])

            except ValueError:
                pass

    if existing_wmap is None:
        wmap = SourceGraphWMAP()
    else:
        wmap = SourceGraphWMAP(existing_wmap)

    for value, _ in vocab.most_common():
        wmap.get_or_add_value(value)

    return wmap


def wmap_stdin(wmap, out):

    dmrs = ''

    while True:
        try:
            dmrs_line = raw_input().decode('utf-8').strip()

            if dmrs_line.startswith('<dmrs'):
                dmrs = dmrs_line

            elif dmrs_line.startswith('</dmrs>'):
                dmrs += dmrs_line

                parser = xml.XMLParser(encoding='utf-8')
                dmrs_xml = xml.fromstring(dmrs.encode('utf-8'), parser=parser)
                wdmrs = wmap.wmap_sentence(dmrs_xml)
                out.write('%s\n\n' % xml.tostring(wdmrs, encoding='utf-8'))

            else:
                dmrs += dmrs_line

        except EOFError:
            break


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='DMRS vocabulary extraction and ID mapping tool.')

    parser.add_argument('-v', '--vocab_extract', default=None,
                        help='Extract DMRS vocabulary (node and edge labels) from DMRS. '
                             'If "-" is specified, input will be read from stdin.')

    parser.add_argument('-c', '--create_wmap', default=None,
                        help='Create a WMAP from a vocabulary file. '
                             'The file can be a concatenation of several vocabulary files')

    parser.add_argument('-w', '--wmap', default=None, help='Existing WMAP file. Required for mapping.')

    parser.add_argument('-m', '--map', default=None,
                        help='Map labels to numeric IDs using an existing word map dictionary. ')

    parser.add_argument('output', help='Output file (vocabulary, WMAP file, or DMRS with ID mapped labels). '
                                       'If "-" is specified, output will be written to stdout.')

    args = parser.parse_args()

    if args.output == '-':
        out = sys.stdout
    else:
        out = open(args.output, 'wb')

    if args.vocab_extract is not None:

        vocab_extractor = SourceGraphVocab()

        if args.vocab_extract == '-':
            vocab_extract_stdin(vocab_extractor)

        else:
            dmrs_list = read_file(args.vocab_extract)
            for dmrs in dmrs_list:
                parser = xml.XMLParser(encoding='utf-8')
                dmrs_xml = xml.fromstring(dmrs.encode('utf-8'), parser=parser)
                vocab_extractor.extract_sentence(dmrs_xml)

        out.write(str(vocab_extractor))

    elif args.create_wmap is not None:

        wmap = create_wmap(args.create_wmap, existing_wmap=args.wmap)
        out.write(str(wmap))

    elif args.map is not None and args.wmap is not None:
        wmap = SourceGraphWMAP(args.wmap)

        if args.wmap == '-':
            wmap_stdin(wmap, out)

        else:
            dmrs_list = read_file(args.map)
            for dmrs in dmrs_list:
                parser = xml.XMLParser(encoding='utf-8')
                dmrs_xml = xml.fromstring(dmrs.encode('utf-8'), parser=parser)

                if empty(dmrs_xml):
                    out.write('%s\n\n' % dmrs)
                else:
                    wdmrs = wmap.wmap_sentence(dmrs_xml)
                    out.write('%s\n\n' % xml.tostring(wdmrs, encoding='utf-8'))

    if args.output != '-':
        out.close()

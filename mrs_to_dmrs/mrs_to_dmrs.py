#!/usr/bin/python

import os
import sys
import errno
import argparse
import xml.etree.ElementTree as xml

from delphin.mrs import simplemrs, dmrx
from delphin._exceptions import XmrsDeserializationError as XDE

def extract_ace_mrs(file_content):
    mrs_chunks = file_content.split('\n\n')
    return ['\n'.join(mrs_chunk.strip().split('\n')[1:]) if mrs_chunk.strip().startswith('SENT') else None for mrs_chunk in mrs_chunks]


def extract_mrs_line(file_content):
    return [line if not line.startswith('SKIP:') else None for line in file_content.split('\n')]


def read_file(filename, file_format='ace'):
    with open(filename, 'rb') as f:
        content = f.read().decode('utf-8').strip()

        if file_format == 'ace':
            return extract_ace_mrs(content)
        elif file_format == 'line':
            return extract_mrs_line(content)
        else:
            raise NotImplementedError("File format '%s' not supported" % file_format)


def read_dir(dirname, file_format='ace', file_suffix='.dmrs'):
    filenames = [os.path.join(dirname, filename) for filename in os.listdir(dirname)]
    return dict((filename + file_suffix, read_file(filename, file_format)) for filename in filenames)


def write_file(filename, dmrs_list):
    with open(filename, 'wb') as f:
        f.write('\n\n'.join(dmrs_list))


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            logging.exception("Error creating directory: %s" % path)
            raise


def mrs_to_dmrs(mrs, ignore_errors=False):
    if mrs is None or mrs == '' or mrs.startswith('SKIP'):
        return '<dmrs></dmrs>'

    try:
        simplemrs_repr = simplemrs.loads_one(mrs)
        dmrs_string = dmrx.dumps_one(simplemrs_repr, pretty_print=True)

        parser = xml.XMLParser(encoding='utf-8')
        dmrs_xml = xml.fromstring(dmrs_string.encode('utf-8'), parser=parser)[0]
        return xml.tostring(dmrs_xml, encoding='utf-8')
    
    except XDE:
        return '<dmrs></dmrs>'


def dmrs_modify(dmrs_string):
    # Load DMRS into XML
    parser = xml.XMLParser(encoding='utf-8')
    dmrs_xml = xml.fromstring(dmrs_string, parser=parser)[0]

    return xml.tostring(dmrs_xml, encoding='utf-8')
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='MRS to DMRS converter.')
    parser.add_argument('-i', '--input', default='-', help='Specify input file or directory. If left empty, program will read MRS from stdin, one per line.')
    parser.add_argument('-o', '--output', default='-', help='Specify output file or directory. Output will mimic input to decide whether to create a file or directory. If left empty, program will read MRS from stdin, one per line.')
    parser.add_argument('-f', '--format', default='ace', choices=['ace', 'line'], help='Format of the MRS file(s).')
    parser.add_argument('--suffix', default='.dmrs')

    args = parser.parse_args()

    if args.input == '-':

        if args.output == '-':
            output = sys.stdout
        else:
            output = open(args.output, 'wb')

        while True:
            try:
                mrs = raw_input().decode('utf-8').strip()
                dmrs = mrs_to_dmrs(mrs)
                output.write('%s\n\n' % dmrs)

            except EOFError:
                break

    elif os.path.isfile(args.input):
        mrs_list = read_file(args.input, args.format)

        if args.output == '-':
            out = sys.stdout
        else:
            out = open(args.output, 'wb')

        for mrs in mrs_list:
            out.write('%s\n\n' %(mrs_to_dmrs(mrs)))

        if not args.output == '-':
            out.close()

    elif os.path.isdir(args.input):
        mrs_dict = read_dir(args.input, args.format, args.suffix)
        dmrs_dict = dict((filename, mrs_to_dmrs(mrs)) for filename, mrs in mrs_dict.items())

        if args.output == '-':
            for _, dmrs_list in dmrs_dict.items():
                sys.stdout.write('%s\n\n' % '\n\n'.join(dmrs_list))

        else:
            make_sure_path_exists(args.output)
            for filename, dmrs_list in dmrs_dict.items():
                write_file(filename, dmrs_list)

    else:
        print "Can't read input: %s" % args.input
        sys.exit()



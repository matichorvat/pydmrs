from collections import Counter


class BaseVocab(object):

    def __init__(self):
        self.vocab_freq = Counter()

    def __str__(self):
        out = ''
        for item, freq in self.vocab_freq.most_common():
            out += '%s\t%d\n' % (item.encode('utf-8'), freq)

        return out

    def extract(self, dataset):
        for sentence in dataset:
            self.extract_sentence(sentence)

    def extract_sentence(self, sentence_dmrs):
        raise NotImplementedError('extract_sentence method not implemented.')

    def get_freq(self):
        return self.vocab_freq

    def write_vocab(self, filename):
        with open(filename, 'wb') as fp:
            for item, freq in self.vocab_freq.most_common():
                fp.write('%s\t%d\n' % (item.encode('utf-8'), freq))


class SourceGraphVocab(BaseVocab):

    def __init__(self):
        super(SourceGraphVocab, self).__init__()

    def extract_sentence(self, sentence_dmrs):
        vocab = Counter()

        if sentence_dmrs is None:
            return vocab

        for entity in sentence_dmrs:

            if entity.tag == 'node':
                node_label = entity.attrib.get('label')
                if node_label is not None:
                    vocab[node_label] += 1

            elif entity.tag == 'link':
                edge_label = entity.attrib.get('label')
                if edge_label is not None:
                    vocab[edge_label] += 1

        self.vocab_freq += vocab
        return vocab


class SourceGraphCargVocab(BaseVocab):

    def __init__(self):
        super(SourceGraphCargVocab, self).__init__()

    def extract_sentence(self, sentence_dmrs):
        vocab = Counter()

        if sentence_dmrs is None:
            return vocab

        for entity in sentence_dmrs:

            if entity.tag == 'node':
                carg = entity.attrib.get('carg')
                if carg is not None:
                    vocab[carg] += 1

        self.vocab_freq = + vocab
        return vocab
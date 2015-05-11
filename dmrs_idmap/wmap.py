
def load_wmap(filename):
    wmap = dict()

    with open(filename, 'rb') as fp:
        for line in fp:
            entry = line.split()

            if len(entry) != 2:
                continue

            try:
                wmap[entry[1]] = int(entry[0])

            except ValueError:
                pass

    return wmap


class BaseWMAP(object):

    def __init__(self, existing_wmap_filename=None):
        self.wmap = dict()

        if existing_wmap_filename is not None:
            self.wmap = load_wmap(existing_wmap_filename)
            self.next_id = max(self.wmap.values()) + 1
        else:
            self.next_id = 0

    def __str__(self):
        inv_wmap = {v: k for k, v in self.wmap.items()}

        out = ''
        for word_id, item in sorted(inv_wmap.items()):
            out += '%d\t%s\n' % (word_id, item.encode('utf-8'))

        return out

    def wmap(self, dataset):
        for sentence in dataset:
            self.wmap_sentence(sentence)

    def wmap_sentence(self, sentence_dmrs):
        raise NotImplementedError('sentence_wmap is not implemented.')

    def get_or_add_value(self, value):
        if value not in self.wmap:
            self.wmap[value] = self.next_id
            self.next_id += 1

        return self.wmap[value]

    def get_wmap(self):
        return self.wmap

    def write_wmap(self, filename):
        inv_wmap = {v: k for k, v in self.wmap.items()}

        with open(filename, 'wb') as fp:
            for word_id, item in sorted(inv_wmap.items()):
                fp.write('%d\t%s\n' % (word_id, item.encode('utf-8')))


class SourceGraphWMAP(BaseWMAP):

    def wmap_sentence(self, sentence_dmrs):

        if sentence_dmrs is None:
            return

        for entity in sentence_dmrs:
            label = entity.attrib.get('label')

            if label is not None:
                entity.attrib['label_idx'] = str(self.get_or_add_value(label))

        return sentence_dmrs
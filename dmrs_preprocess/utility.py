from itertools import tee, izip


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


def triple(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b, c = tee(iterable, 3)
    next(b, None)
    next(c, None)
    next(c, None)

    return izip(a, b, c)


def contains_sublist(lst, sublst):
    n = len(sublst)
    return any((sublst == lst[i:i+n]) for i in xrange(len(lst)-n+1))


def empty(dmrs_xml):
    for _ in dmrs_xml:
        return False

    return True


def load_wmap(filename):
    wmap = dict()

    with open(filename, 'rb') as fp:
        for line in fp:
            entry = line.strip().split('\t')

            assert len(entry) == 2

            wmap[entry[1]] = int(entry[0])

    return wmap
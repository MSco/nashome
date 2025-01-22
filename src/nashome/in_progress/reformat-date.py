#!/usr/bin/env python

"""
"""
import glob
import os

import regex as re
from multiprocessing import Pool

EXTENSION = "pdf"


def extract(filename):
    """
    Try to extract the attachments from all files in cwd
    """
    new_filename = re.sub(r"(\d{4})(\d{2})(\d{2})(.*\.pdf)", r"\1-\2-\3\4", filename)
    print(f'rename {filename} -> {new_filename}')
    os.rename(filename, new_filename)


if __name__ == "__main__":
    # let's do this in parallel, using cpu count as number of threads
    pool = Pool(None)
    res = pool.map(extract, glob.iglob("*.%s" % EXTENSION))
    # need these if we use _async
    pool.close()
    pool.join()
    # 2-element list holding number of files, number of attachments
    numfiles = [sum(i) for i in zip(*res)]
    print("Done: Processed {} files with {} attachments.".format(*numfiles))

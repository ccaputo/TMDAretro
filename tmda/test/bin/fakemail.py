#!/usr/bin/env python2

import sys

print 'FAKE SENDMAIL ARGS:', sys.argv

for line in sys.stdin:
    print line,

sys.exit(0)

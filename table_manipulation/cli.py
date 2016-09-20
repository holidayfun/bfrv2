#!/usr/bin/env python

import argparse
#import fileinput
from subprocess import call
import sys
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="runtime cli")
    parser.add_argument('-ip', dest='ip', default=None, type=str)
    parser.add_argument('-port', dest='port', default=10000, type=int)
    parser.add_argument('-switch', dest='switch', type=int)
    args = parser.parse_args()

    if args.switch is None and args.ip is None:
        print('ip oder switch Nummer muss angegeben werden')
        sys.exit(1)
    if args.ip is not None:
        ip = args.ip
    else:
        ip = '100.0.0.{0}'.format(100+2*args.switch)

    port = args.port
    print('Connectiong to {0}:{1}'.format(ip, port))

    print(call(['/home/hartmann/behavioral-model/targets/bfrv2/cli/sswitch_CLI.py',
                #'--pre', 'SimplePreLAG',
                '--thrift-port', str(port),
                '--thrift-ip', ip],
                stdin=sys.stdin))

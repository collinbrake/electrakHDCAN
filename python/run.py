import argparse
import signal
import sys

from gotoposition import build_parser, main as run_position_command


if __name__ == "__main__":
    parser = build_parser()
    signal.signal(signal.SIGINT, signal.default_int_handler)
    try:
        run_position_command(parser.parse_args())
    except KeyboardInterrupt:
        sys.exit(0)
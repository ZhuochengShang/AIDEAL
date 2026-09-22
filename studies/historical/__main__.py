"""Optional historical reports; these commands do not run new evaluations."""
import argparse
import json
from pathlib import Path

from .reporting import reproduce
from .status import study_status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('reproduce')
    p = sub.add_parser('status')
    p.add_argument('--repo', required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    result = reproduce(root) if args.command == 'reproduce' else study_status(root, args.repo)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

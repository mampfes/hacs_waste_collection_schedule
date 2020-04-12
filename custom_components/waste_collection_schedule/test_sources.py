#!/usr/bin/python3

import argparse
import os
import pathlib
import importlib


def main():
    parser = argparse.ArgumentParser(description='Test sources.')
    parser.add_argument("-s", "--source", action='append', help="Test given source file")
    parser.add_argument("-l", "--list", action="store_true", help="List retrieved entries")
    args = parser.parse_args()

    if args.source is not None:
        files = args.source
    else:
        files = filter(lambda x: x != "__init__", map(lambda x: x.stem, pathlib.Path("package/source").glob("*.py")))

    for f in files:
        # iterate through all *.py files in package/source
        print(f"Testing source {f} ...")
        module = importlib.import_module(f"package.source.{f}")
        # create source
        for name, tc in module.TEST_CASES.items():
            # run through all test-cases
            source = module.Source(**tc)
            result = source.fetch()
            print(f"  found {len(result)} entries for {name}")
            if args.list:
                for x in result:
                    print(f"    {x.date.isoformat()}: {x.type}")


if __name__ == "__main__":
    main()

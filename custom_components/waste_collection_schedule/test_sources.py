#!/usr/bin/python3

import os
import pathlib
import importlib


def main():
    for f in pathlib.Path("package/source").glob("*.py"):
        # iterate through all *.py files in package/source
        if f.stem != "__init__":
            # ignore __init__.py
            print(f"Testing source {f.stem} ...")
            module = importlib.import_module(f"package.source.{f.stem}")
            # create source
            for name, tc in module.TEST_CASES.items():
                # run through all test-cases
                source = module.Source(**tc)
                result = source.fetch()
                print(f"  found {len(result)} entries for {name}")


if __name__ == "__main__":
    main()


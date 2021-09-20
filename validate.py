#!/usr/bin/env python3

import json
import sys

from jsonschema import validate, draft7_format_checker, ValidationError


def run(args):
    try:
        instance = json.load(args.instance)
        schema = json.load(args.schema)
    except json.decoder.JSONDecodeError as why:
        sys.stderr.write(f"JSON decoding error: {why}\n")
        sys.exit(1)
    try:
        validate(instance, schema, format_checker=draft7_format_checker)
    except ValidationError as why:
        sys.stderr.write(f"{why}\n")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate a JSON file.")
    parser.add_argument("schema", type=open, help="The JSON schema file")
    parser.add_argument("instance", type=open, help="The JSON instance file")
    try:
        args = parser.parse_args()
    except Exception as why:
        sys.stderr.write(f"{why}\n")
        sys.exit(1)
    run(args)

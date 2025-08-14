#! /usr/bin/env python3

import json
import yaml

def main():
    # Open const/name-to-flag.yaml and const/aliases.yaml, read both
    with open('const/name-to-flag.yaml', 'r') as f:
        name_to_flag: dict[str, str] = yaml.safe_load(f)

    with open('const/aliases.yaml', 'r') as f:
        aliases: dict[str, str|list[str]] = yaml.safe_load(f)

    def entries(maybe_list: str|list[str]) -> list[str]:
        return [maybe_list] if isinstance(maybe_list, str) else maybe_list

    # Walk through the aliases map, where keys are talent names, and values are either a single name
    # or a list of names.
    full_flags = name_to_flag | {
        alias: name_to_flag[talent_name]
        for talent_name, alias_values in aliases.items()
        if talent_name in name_to_flag
        for alias in entries(alias_values)
    }

    # Save this map of name => flag into data/full_flags.json
    with open('data/full_flags.json', 'w') as f:
        json.dump(full_flags, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()

import sys
import os
import argparse

def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder', type=str, required=True, help="Folder with files.")
    parser.add_argument('-r', '--rename-file', type=str, required=True, help="Rename file.")
    args = parser.parse_args()
    return args


def main():
    args = parseargs()

    with open(args.rename_file) as f:
        for line in f.readlines():
            orig_name, rename_name = line.split()
            os.rename(os.path.join(args.folder, orig_name), os.path.join(args.folder, rename_name))


if __name__ == '__main__':
    sys.exit(main())

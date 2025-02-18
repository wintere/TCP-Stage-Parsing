from multiprocessing import Process
import os
import xmlparser
import argparse
import pandas as pd



# Traverse a folder of EEBO-TCP P4 XML Files
def traverse(parser, target_dirs):
    rows = []
    for collection in target_dirs:
        for root, dirs, files in os.walk(collection):
            for file in files:
                fp = os.path.join(root, file)
                if file.lower().endswith("p4.xml"):
                    row = parser.xml_to_row(fp, file)
                    if row:
                        rows.append(row)
    return rows


def main():
    args = argparse.ArgumentParser(
        prog="BatchProess",
        description="Processes a list of folders of XML files",
    )
    args.add_argument(
        "-s", "--nostage", action='store_true',
    )
    args.add_argument("-o", "--outfile", help="CSV output filename", type=str)
    args.add_argument("-f", "--folders", help="list of input folders", nargs="+")
    opts = args.parse_args()
    parser = xmlparser.XMLProcessor(nostage=opts.nostage)
    rows = traverse(parser, opts.folders)
    if rows:
        metadata = pd.DataFrame.from_records(rows).sort_values(by='FILE')
        metadata.to_csv(open(opts.outfile, mode="wb"), encoding="utf-8", lineterminator="\n", index=False)
    else:
        print("No TCP-P4 XML files found in folders", opts.folders)
        exit()

if __name__ == "__main__":
    main()
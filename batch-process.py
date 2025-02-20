from multiprocessing import Process
import os
import xmlparser
import argparse
import pandas as pd


# Traverse a folder of EEBO-TCP P4 XML Files
def traverse(parser, target_dirs):
    rows, ignored, parsed, failed = [], 0, 0, 0
    for collection in target_dirs:
        for root, dirs, files in os.walk(collection):
            for file in files:
                fp = os.path.join(root, file)
                if file.lower().endswith("p4.xml"):
                    row = parser.xml_to_row(fp, file)
                    if row:
                        rows.append(row)
                        parsed += 1
                    else:
                        failed += 1
                else:
                    ignored+=1
                if parsed % 1000 == 0: # Log every 1000 files parsed
                    print("Parsed", parsed, "files...")
    print("Finished processing!")
    print("Parsed", parsed, "files")
    print("Ignored", ignored, "files")
    print("Failed to parse", failed, "files")
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
        metadata = pd.DataFrame.from_records(rows).sort_index(axis=1).sort_values(by='FILE')
        # Put key columns first
        metadata.insert(0, "TITLE", metadata.pop("TITLE"))
        metadata.insert(0, "AUTHOR", metadata.pop("AUTHOR"))
        metadata.insert(0, "TCP", metadata.pop("TCP"))

        metadata.to_csv(open(opts.outfile, mode="wb"), encoding="utf-8", lineterminator="\n", index=False)
    else:
        print("No TCP-P4 XML files found in folders", opts.folders)
        exit()

if __name__ == "__main__":
    main()
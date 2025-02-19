from multiprocessing import Process
import os
import xmlparser
import argparse
import pandas as pd
from lxml import etree
import xmlparser

def process_rows(parser, files):
    rows = []
    for f in files:
        rows.append(xmlparser.xml_to_row(parser, f))
    return rows

# Traverse a folder of EEBO-TCP P4 XML Files
def traverse(target_dirs, proc=0):
    xml_paths = []
    for collection in target_dirs:
        for root, dirs, files in os.walk(collection):
            for file in files:
                fp = os.path.join(root, file)
                if file.lower().endswith("p4.xml"):
                    xml_paths.append(fp)
    # Serial                  
    if proc == 0:
        rows = []
        parser = etree.XMLParser(remove_blank_text=True, encoding='utf-8')
        for fp in xml_paths:
            row = parser.xml_to_row(fp)
            if row:
                rows.append(row)
    else:
        parsers = [etree.XMLParser(remove_blank_text=True, encoding='utf-8') for i in range(proc)]
        processes = []
        inputs = xml_paths[0]
        for i in range(proc):
            p = Process(target=process_rows, args=(parsers[i], inputs[i]))
            processes.append(p)
            p.start()
        
        for p in processes:
            p.join()

    return rows


def main():
    args = argparse.ArgumentParser(
        prog="BatchProcess",
        description="Processes a list of folders of XML files",
    )
    args.add_argument(
        "-m", "--multiprocessing", type=int
    )
    args.add_argument("-o", "--outfile", help="CSV output filename", type=str)
    args.add_argument("-f", "--folders", help="list of input folders", nargs="+")
    opts = args.parse_args()
    processes = opts.multiprocessing # Get # of threads
    rows = traverse(opts.folders, proc=processes)

    if rows:
        metadata = pd.DataFrame.from_records(rows).sort_values(by='FILE')
        metadata.to_csv(open(opts.outfile, mode="wb"), encoding="utf-8", lineterminator="\n", index=False)
    else:
        print("No TCP-P4 XML files found in folders", opts.folders)
        exit()

if __name__ == "__main__":
    main()
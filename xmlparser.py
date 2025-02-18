from lxml import etree
import re

HAS_DIGITS = re.compile(r".*[0-9]+.*")
DATES = re.compile(r"[1-2][0-9][0-9][0-9]")
PHASE = re.compile("(EEBO-TCP PHASE [1-2])")

# Helper function: regex for stripping dates
def clean_date(d):
    # Remove trailing period
    found = re.findall(DATES, d)
    if len(found) == 1:
        return found[0]
    # Prefer earlier (stated) rather than inferred dates
    elif len(found) >= 2:
        return found[0]
    else:
        return d.rstrip(".")

# Helper function for semicolon-separated metadata
def add_with_seps(d, k, v):
    cur = d.get(k)
    if cur:
        if v not in cur:
            d[k] = cur + "; " + v
    else:
        d[k] = v

class XMLProcessor():

    def __init__(self, nostage=False):
        self.parser = etree.XMLParser(remove_blank_text=True, 
                                               encoding='utf-8')
        self.nostage = nostage

    # Transforms each XML file into one row of metadata
    def xml_to_row(self, path, fn):
        row_dict = {}
        row_dict["FILE"] = fn
        row_dict["TCP"] = ".".join(fn.split(".")[:-2])
        # Open (and close) XML file
        with open(path, encoding="utf-8") as fp:
            # Parse XML file using XPATH (suboptimal)
            tree = etree.parse(fp, self.parser)
            r = tree.getroot()
            # Get EEBO-specific info
            for node in r.xpath("//IDG"):
                if node.attrib.get("R").lower() == "um":
                    row_dict["TCP"] = node.attrib.get("ID")
            # Get EEBO phase information
            for node in r.xpath("//DATE"):
                if node.text is not None and "EEBO-TCP" in node.text.upper():
                    eebo_phase = re.findall(PHASE, node.text.upper())
                    if eebo_phase:
                        row_dict["PHASE"] = eebo_phase[0]
            for t in r.xpath("//TITLE"):
                row_dict["TITLE"] = t.text
            for author in r.xpath("//AUTHOR"):
                add_with_seps(row_dict, "AUTHOR", author.text)
            for publisher in r.xpath("//BIBLFULL//PUBLICATIONSTMT//PUBLISHER"):
                add_with_seps(row_dict, "PUBLISHER", publisher.text)
            for d in r.xpath("//BIBLFULL//PUBLICATIONSTMT//DATE"):
                row_dict["RAW_DATE"] =  d.text
                if re.match(HAS_DIGITS, d.text):
                    # Populated "cleaned" numeric date by regex
                    row_dict["CLEANED_DATE"] = clean_date(d.text)
            for z in r.xpath("//BIBLFULL//PUBPLACE"):
                place = z.text.rstrip(":, ")
                row_dict["PUBPLACE"] = place
            for keyword in r.xpath("//KEYWORDS//TERM"):
                add_with_seps(row_dict, "KEYWORDS", keyword.text)
            # Get full publication information
            full_pub = ""
            for ps in r.xpath("//BIBLFULL//PUBLICATIONSTMT"):
                for pub in ps.iterchildren():
                    if pub.text:
                        full_pub += pub.text
                    if pub.tail:
                        full_pub += pub.tail
            if full_pub:
                row_dict["PUBLICATION"] = full_pub
            # Get key cross-dataset identifiers like ETC, STC, Gale
            for idno in r.xpath("//IDNO"):
                typ = idno.attrib.get("TYPE").upper()
                raw_id = idno.text
                # This hideous block of code exist to identify non-STC identifiers in STC tags (present in EEBO, not ECCO)
                if typ == "STC":
                    if raw_id.startswith("ESTC "):
                        add_with_seps(row_dict, "ESTC", raw_id[5:])
                    elif raw_id.startswith("Wing "):
                        add_with_seps(row_dict, "Wing", raw_id[5:])
                    elif raw_id.startswith("Thomason"):
                        add_with_seps(row_dict, "Thomason", raw_id)
                    elif raw_id.startswith("Interim Tract Supplement Guide"):
                        add_with_seps(row_dict, "Interim_Tract_Supplement_Guide", raw_id[31:])
                    elif raw_id.startswith("Evans "):
                        add_with_seps(row_dict, "Evans", raw_id[6:])
                    elif raw_id.startswith("STC") == False:
                        add_with_seps(row_dict, "OTHER_IDS", raw_id)
                    else:
                        add_with_seps(row_dict,typ, raw_id)
                # Straightforward ids
                elif typ in ["PROQUEST", "VID", "OCLC", "EEBO CITATION", "GALEDOCNO", "DOCNO",
                            "ESTC", "IMAGESETID", "CONTENTSET"]:
                    add_with_seps(row_dict, typ, raw_id)
                else: 
                    add_with_seps(row_dict, "OTHER_IDS", typ + " " + raw_id)

            # Get bilbiographic notes from the TCP compilers (superceded by ESTC where possible)
            for pub_statement in r.xpath("//BIBLFULL//NOTESSTMT//NOTE"):
                note = pub_statement.text
                add_with_seps(row_dict, "TCP_NOTES", note)
                # Hack: Isolate lines related to physical holdings
                if "library" in note.lower() or "original" in note.lower() or "reproduction" in note.lower() or "archive" in note.lower() or "museum" in note.lower():
                    add_with_seps(row_dict, "TCP_LOCATION", note)
            for stc in r.xpath("//STC"):
                if stc.attrib.get("T") == "C" and "ESTC" not in row_dict: # God knows why, this is ESTC
                    add_with_seps(row_dict, "ESTC", stc.text.upper())
            # Utility: Collection Label
            if fn.upper().startswith("K"):
                row_dict["PHASE"] = "ECCO"
            if fn.upper().startswith("N"):
                row_dict["PHASE"] = "EVANS"
            # If stage processing is enabled, get stage specific attributes
            if not self.nostage:
                for div in r.xpath("//*[starts-with(name(), 'DIV') or starts-with(name(), 'div')]"):
                    div_type = div.attrib.get("TYPE").lower()
                    if "dramatis" in div_type:
                        row_dict["XML_DRAMATIS_PERSONAE"] = True
                    elif div_type == "play":
                        row_dict["XML_PLAY"] = True
                    elif div_type == "masque":
                        row_dict["XML_MASQUE"] = True
                    elif div_type == "opera":
                        row_dict["XML_OPERA"] = True
                    elif div_type == "entertainment":
                        row_dict["XML_ENTERTAINMENT"] = True
        return row_dict

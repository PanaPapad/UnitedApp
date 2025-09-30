from docling.document_converter import DocumentConverter
import re
import pandas as pd
from io import StringIO

def covert_to_md(url):
    "Converts a url to an md table"
    converter = DocumentConverter()
    result = converter.convert(url)
    mark = result.document.export_to_markdown()

    # only filter the tables (start with |)
    filtered = "\n".join(
        line for line in mark.splitlines() if line.startswith("|")
    )

    print(filtered)
    return filtered


def md_to_csv(md_table, out_file):
    rows = []
    for line in md_table.splitlines():
        line = line.strip()
        # skip separator lines (like ----)
        if set(line) <= {"|", "-", " "}:
            continue
        # remove leading/trailing | and collapse multiple spaces
        line = line.strip("|")
        line = re.sub(r"\s+", " ", line)
        rows.append(line)

    cleaned = "\n".join(rows)

    # Now parse into DataFrame
    df = pd.read_csv(StringIO(cleaned), sep="|")
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    df.to_csv(out_file, index=False)
    return df

url = "https://www.fotmob.com/teams/10204/squad/brighton-hove-albion"
team_name = url.rstrip("/").split("/")[-1]
md_table = covert_to_md(url)
md_to_csv(md_table, f"Data/{team_name}.csv")

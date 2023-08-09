def genoversify(obj):
    if "accession_id" in obj:
        obj["id"] = obj["accession_id"]
    elif "id" in obj:
        obj["id"] = str(obj["id"])

    if "chr" in obj:
        obj["chr"] = obj["chr"].removeprefix("chr")

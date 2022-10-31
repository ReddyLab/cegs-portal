def genoversify(obj):
    if "id" in obj:
        obj["id"] = str(obj["id"])
    if "chr" in obj:
        obj["chr"] = obj["chr"].removeprefix("chr")

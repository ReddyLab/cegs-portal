# Accession IDs

Most objects in the database have an accession ID, which is a stable ID that can be used to refer to the object. It should be independent of the database ID and retained across data loads.

The format of the accession id is DCPYYYYXXXXXXXX. DCP stands for "Duke CCGR Portal", Y is a capital letter and X is a hexadecimal digit (0-9, A-F). The Ys represent the kind of thing the ID belongs to and the Xs are the ID number. Hexadecimal digits were selected because they allow mfor ore IDs than just 0-9 but without having to worry about "bad words" being spelled (in English, anyway).

These are the current items with Accession IDs:

| Type                     | Abbreviation |
|-------------------------------|---------|
| Experiment                       | EXPR |
| Regulatory Effect                | RE   |
| Gene                             | GENE |
| Transcript                       | T    |
| Exon                             | EXON |
| Candidate cis-regulatory element | CCRE |
| Guide RNA                        | GRNA |
| DNase I hypersensitive site      | DHS  |

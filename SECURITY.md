# Security

## Reporting a vulnerability

Please report security problems privately, through
[GitHub's private vulnerability reporting](https://github.com/enestanerr/prove/security/advisories/new),
not in a public issue. You will get an answer within a few days.

## What Prove does with your documents

- `provecheck` runs on your machine. It reads the document you give it and writes its
  working files and reports next to it. It sends the document nowhere.
- In skill mode, the model that reads the document is the Claude you are already
  talking to. Prove adds no service of its own.
- The only network use is `provecheck sources`, and only when you run it. It asks
  Crossref, DataCite, doi.org and arXiv about the identifiers cited in the document,
  and fetches the URLs the document cites. `--offline` turns this off.
- Because a document chooses which URLs get fetched, source checks refuse addresses on
  the local machine and on private networks.
- The HTML report is one self-contained file with no scripts and no external requests.
  Text from the document is escaped before it is written into it.

## Scope

In scope: anything that lets a document make `provecheck` read or write outside the
folder it was given, reach a private network address, run code, or produce a report
that executes script. A wrong verdict is a bug, not a vulnerability; use the
"Wrong verdict" issue form for those.

## Supported versions

The latest release.

# Two worked examples

## 1. A quarterly report (English, a table and a chart)

Page 1 says: *Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%.*
Page 2 has a table of orders by region and the sentence *East accounted for 28.3% of
orders.* Page 3 has a bar chart (Figure 2, axis 0 to 400, USD thousands) and the
sentence *Q3 marketing spend reached 350k.*

```json
{
  "schema": "prove.claims.v1",
  "document": {"path": "report.pdf", "locale": "en"},
  "numbers": [
    {"id": "n1", "text": "2.10M", "value": "2100000", "decimals": 2, "unit": "USD", "exact": null,
     "loc": {"page": 1, "quote": "Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%."}},
    {"id": "n2", "text": "2.30M", "value": "2300000", "decimals": 2, "unit": "USD", "exact": null,
     "loc": {"page": 1, "quote": "Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%."}},
    {"id": "n3", "text": "14%", "value": "14", "decimals": 0, "unit": "%", "exact": null,
     "loc": {"page": 1, "quote": "Revenue rose from $2.10M in Q2 to $2.30M in Q3, up 14%."}},
    {"id": "n4", "text": "1,204", "value": "1204", "decimals": 0, "unit": "orders", "exact": "count",
     "loc": {"page": 2, "quote": "North | 1,204"}},
    {"id": "n5", "text": "988", "value": "988", "decimals": 0, "unit": "orders", "exact": "count",
     "loc": {"page": 2, "quote": "South | 988"}},
    {"id": "n6", "text": "1,356", "value": "1356", "decimals": 0, "unit": "orders", "exact": "count",
     "loc": {"page": 2, "quote": "East | 1,356"}},
    {"id": "n7", "text": "1,244", "value": "1244", "decimals": 0, "unit": "orders", "exact": "count",
     "loc": {"page": 2, "quote": "West | 1,244"}},
    {"id": "n8", "text": "4,812", "value": "4812", "decimals": 0, "unit": "orders", "exact": "count",
     "loc": {"page": 2, "quote": "Total | 4,812"}},
    {"id": "n9", "text": "28.3%", "value": "28.3", "decimals": 1, "unit": "%", "exact": null,
     "loc": {"page": 2, "quote": "East accounted for 28.3% of orders"}},
    {"id": "n10", "text": "350", "value": "350", "decimals": 0, "unit": "k USD", "exact": null,
     "loc": {"page": 3, "quote": "Q3 marketing spend reached 350k"}}
  ],
  "claims": [
    {"id": "c1", "kind": "derived", "target": "n3", "hedge": null,
     "derivation": {"op": "pct_change", "args": [{"ref": "n1"}, {"ref": "n2"}]},
     "say": "The growth figure should be the change from $2.10M to $2.30M."},
    {"id": "c2", "kind": "derived", "target": "n8", "hedge": null,
     "derivation": {"op": "sum", "args": [{"ref": "n4"}, {"ref": "n5"}, {"ref": "n6"}, {"ref": "n7"}]},
     "say": "The total row should be the sum of the four regions."},
    {"id": "c3", "kind": "derived", "target": "n9", "hedge": null,
     "derivation": {"op": "pct_of", "args": [{"ref": "n6"},
        {"op": "sum", "args": [{"ref": "n4"}, {"ref": "n5"}, {"ref": "n6"}, {"ref": "n7"}]}]},
     "say": "East's share should be its orders divided by the sum of all regions."},
    {"id": "c4", "kind": "chart", "check": "text_vs_chart", "target": "n10",
     "chart": "g1", "mark": {"label": "Q3"},
     "say": "The prose figure for Q3 marketing spend should match the Q3 bar in Figure 2."}
  ],
  "charts": [
    {"id": "g1", "loc": {"page": 3, "figure": "Figure 2"}, "type": "bar",
     "image": "prove-work/crops/g1.png",
     "y_axis": {"min": "0", "max": "400", "scale": "linear", "unit": "USD thousands"},
     "marks": [
       {"label": "Q3", "read_a": {"lo": "300", "hi": "320"}, "read_b": {"lo": "302", "hi": "318"},
        "printed_label": null}
     ],
     "notes": []}
  ],
  "sources": [],
  "skipped": [
    {"text": "2026", "reason": "year"},
    {"text": "2", "loc": {"page": 3, "quote": "Figure 2"}, "reason": "figure number"}
  ]
}
```

Things to notice:

- The share in `c3` is checked against the **sum of the rows**, not against the printed
  total. The printed total is itself under check in `c2`. Do not build one claim on a
  number that another claim doubts when the parts are available.
- The table counts are `exact: "count"`. The revenue figures are rounded, so `exact` is
  `null`.
- `350k` against an axis in thousands is recorded as `350` with `unit: "k USD"`.
- What `provecheck` prints for this file is the answer. For `c1` it prints
  `2.30M ÷ 2.10M − 1 = 9.52%; possible range 9.03%–10.02%; the document says 14%` and
  the verdict `contradicted`. Had the document printed `2.1M` and `2.3M`, the range
  would be 4.65%–14.63% and the verdict `suspect`. That difference is the point of the
  tool: you do not decide it.

## 2. A Turkish memo (European number format, hedge, table in thousands)

*Gelir 2,10 milyon TL'den 2,30 milyon TL'ye çıktı, artış yaklaşık %10.*
A table headed "bin TL" lists `Kira | 1.250,5` and `Maaş | 3.400,0` and
`Toplam | 4.650,5`. The text says *Toplam gider 4,65 milyon TL.*

```json
{
  "schema": "prove.claims.v1",
  "document": {"path": "not.md", "locale": "tr"},
  "numbers": [
    {"id": "n1", "text": "2,10 milyon", "value": "2100000", "decimals": 2, "unit": "TL", "exact": null,
     "loc": {"page": 1, "quote": "Gelir 2,10 milyon TL'den 2,30 milyon TL'ye çıktı"}},
    {"id": "n2", "text": "2,30 milyon", "value": "2300000", "decimals": 2, "unit": "TL", "exact": null,
     "loc": {"page": 1, "quote": "Gelir 2,10 milyon TL'den 2,30 milyon TL'ye çıktı"}},
    {"id": "n3", "text": "%10", "value": "10", "decimals": 0, "unit": "%", "exact": null,
     "loc": {"page": 1, "quote": "artış yaklaşık %10"}},
    {"id": "n4", "text": "1.250,5", "value": "1250500", "decimals": 1, "unit": "TL", "scale": "1000",
     "exact": null, "loc": {"page": 1, "quote": "Kira | 1.250,5"}},
    {"id": "n5", "text": "3.400,0", "value": "3400000", "decimals": 1, "unit": "TL", "scale": "1000",
     "exact": null, "loc": {"page": 1, "quote": "Maaş | 3.400,0"}},
    {"id": "n6", "text": "4.650,5", "value": "4650500", "decimals": 1, "unit": "TL", "scale": "1000",
     "exact": null, "loc": {"page": 1, "quote": "Toplam | 4.650,5"}},
    {"id": "n7", "text": "4,65 milyon", "value": "4650000", "decimals": 2, "unit": "TL", "exact": null,
     "loc": {"page": 1, "quote": "Toplam gider 4,65 milyon TL"}}
  ],
  "claims": [
    {"id": "c1", "kind": "derived", "target": "n3", "hedge": "approx",
     "derivation": {"op": "pct_change", "args": [{"ref": "n1"}, {"ref": "n2"}]},
     "say": "Artış, 2,10 milyondan 2,30 milyona değişim olmalı."},
    {"id": "c2", "kind": "derived", "target": "n6", "hedge": null,
     "derivation": {"op": "sum", "args": [{"ref": "n4"}, {"ref": "n5"}]},
     "say": "Toplam satırı iki kalemin toplamı olmalı."},
    {"id": "c3", "kind": "derived", "target": "n7", "hedge": null,
     "derivation": {"op": "eq", "args": [{"ref": "n6"}]},
     "say": "Metindeki toplam gider, tablodaki toplamla aynı olmalı."}
  ],
  "charts": [], "sources": [], "skipped": []
}
```

Things to notice:

- `locale: "tr"` makes `1.250,5` read as 1250.5. With `scale: "1000"` its `value` is
  1250500.
- `yaklaşık` (about) is recorded as `hedge: "approx"`, not ignored.
- `say` is written in the language of the document.
- `c3` is a cross-reference between two prints of one quantity at different precision.

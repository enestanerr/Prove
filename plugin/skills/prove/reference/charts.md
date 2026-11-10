# Reading a chart for Prove

You read the chart. `provecheck` compares your reading with the printed numbers. A
reading is an interval, and it is taken twice.

## Protocol

Do these in order for every chart you check.

1. **Get the image.** For a PDF, the page images are in `prove-work/pages/`. For a
   Markdown or HTML document, the figure is its own image file. Look at it.
2. **Axis first.** Before any mark, write down the value axis: lowest and highest
   labelled tick, linear or log, and the unit as printed ("USD thousands", "%").
   Note whether a bar axis starts at zero.
3. **First reading (`read_a`).** For each mark, find the two gridlines or ticks it lies
   between and estimate where. Give `lo` and `hi` in axis units. The interval must
   contain the true value: when the top of a bar is hard to place, widen it.
4. **Crop.** Cut the plot area out at twice the size:
   `PROVE crop --doc <pdf or image> --page N --box x0,y0,x1,y1 --upscale 2 -o prove-work/crops/g1.png`
   The box is in fractions of the page: `0,0` is the top left, `1,1` the bottom right.
   Keep the value axis and its tick labels inside the crop.
5. **Second reading (`read_b`).** Look at the crop and read every mark again, from the
   gridlines, without looking at your first numbers.
6. **Never copy a printed label into a reading.** If a bar carries the label "350", the
   reading is still where the bar ends on the axis. The label is a printed number:
   put it in `numbers` and check it with `label_vs_mark`.

If the two readings of a mark do not overlap, leave them as they are. `provecheck`
marks it unstable and the check ends unverified. Do not adjust one to fit the other.

## What to write

```json
{"id": "g1", "loc": {"page": 5, "figure": "Figure 2"}, "type": "bar",
 "image": "prove-work/crops/g1.png",
 "y_axis": {"min": "0", "max": "400", "scale": "linear", "unit": "USD thousands"},
 "marks": [
   {"label": "Q3", "series": "Revenue",
    "read_a": {"lo": "300", "hi": "320"}, "read_b": {"lo": "302", "hi": "318"},
    "printed_label": null}
 ],
 "notes": []}
```

- `type`: `bar`, `grouped_bar`, `stacked_bar`, `line`, `pie`, or another plain word.
- `y_axis.min` / `max`: the ends of the value axis, in axis units. A pie has no axis:
  leave `y_axis` out and read each slice as a percentage of the whole.
- `y_axis.multiplier`: only when the axis is in thousands or millions and the number
  you compare with is not. Axis "USD thousands" against the text "$350,000" needs
  `"multiplier": "1000"`. Against the text "350k" recorded as `text: "350"`, it does not.
- `marks[].label` is the category (the x label, the slice name, the point's x value);
  `series` is the legend entry when there is more than one.
- For a stacked bar, read each segment's own height (top minus bottom), not its top.
- `printed_label`: the id of the number printed on the mark, if any.
- `image`: the crop, so the report can show it.
- `notes`: things a reader should know that are not errors: the bar axis does not start
  at zero, two y axes, a log scale, 3-D distortion.

A reading narrower than 2% of the axis span is widened to 2% by `provecheck`. Do not
try to be more precise than the picture allows.

## Chart claims

```json
{"id": "c4", "kind": "chart", "check": "text_vs_chart", "target": "n10",
 "chart": "g1", "mark": {"label": "Q3", "series": "Revenue"},
 "say": "The prose figure for Q3 revenue should match the Q3 bar in Figure 2."}
```

| `check` | Compares | Needs |
| :- | :- | :- |
| `label_vs_mark` | a value printed on or beside the mark with the mark's reading | `target`, `mark` |
| `text_vs_chart` | a number in the prose that the chart depicts | `target`, `mark` |
| `table_vs_chart` | a table cell that the chart depicts | `target`, `mark` |
| `parts_sum` | pie slices or stacked segments with their stated total | `target`, optional `marks` (default: all) |
| `order` | "largest", "smallest", "A above B" with the readings | `mark`, `relation`: `largest`, `smallest`, `gt`, `lt`; `than` for `gt`/`lt` |

The `target` number must be in the same unit as the reading. If the text says "350k"
and the axis is in thousands, record the number as `text: "350"`, `value: "350"`,
`unit: "k USD"`, quoting the sentence that contains "350k".

Numbers that appear only inside the image (tick labels, value labels) are not in the
text scan. Tick labels need no entry. A value label gets a `numbers` entry only if you
check it. Mark it as printed in the figure, and quote the label itself:

```json
{"id": "n21", "text": "68", "value": "68", "decimals": 0, "unit": "%", "exact": null,
 "loc": {"page": 2, "quote": "68", "image": true}}
```

Use `"image": true` only for numbers that are not in the page text. Such a number
cannot be grounded, so its verdicts are tagged `read`.

A chart verdict is `contradicted` only when the printed number and both readings
cannot meet. It is reported with the tag `read`, apart from the computed verdicts.

# Gemeinde Seuzach

Support for waste collection schedules provided by [Gemeinde Seuzach](https://www.seuzach.ch/abfalldaten), Switzerland.

The source combines two kinds of data, both fetched live from the official website on every update — nothing about the actual schedule is hardcoded:

- **Regular collections** ("Regelmässige Abfuhr"): Kehrichtabfuhr (household refuse) and Grünabfuhr (garden waste) are not published as a list of dates. Each runs weekly on a German weekday described only in prose on a linked detail page (e.g. "findet wöchentlich am Dienstag statt"). Grünabfuhr additionally only runs within a described season (e.g. "von März bis November ... erstmals am 2. März und letztmals am 30. November"). Rather than hardcoding the weekday or season, the source resolves the detail-page link for each entry from `https://www.seuzach.ch/abfalldaten` and parses the weekday/season from the live text on every run.
- **Special town-wide collections** ("Besondere Sammeltermine"): Papier-/Kartonsammlung, Sonderabfälle, Häckseldienst, and the Grünabfuhr dates in January/February/December that fall outside the regular season, all published with concrete dates in a table on the same page.

No address or municipality parameter is needed — the whole of Seuzach shares one schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: seuzach_ch
      args: {}
```

## Bin types returned

| Provider description               | Icon              |
|-------------------------------------|--------------------|
| Kehrichtabfuhr                      | `mdi:trash-can`    |
| Grünabfuhr                          | `mdi:flower`       |
| Papier- / Kartonsammlung            | `mdi:package-variant` |
| Sonderabfälle                       | `mdi:biohazard`    |
| Häckseldienst                       | `mdi:flower`       |

Note: holiday-related shifts of individual Kehrichtabfuhr/Grünabfuhr dates (mentioned on the website as being listed in a separate PDF "Recyclingkalender") are not accounted for by this source, since they are only published as a PDF, not in the structured HTML data used here.

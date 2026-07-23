# Gemeinde Muttenz

Support for waste collection schedules provided by [Gemeinde Muttenz](https://www.muttenz.ch/abfalldaten), Switzerland.

The source combines two kinds of data, both fetched live from the official website on every update — nothing about the actual schedule is hardcoded:

- **Regular refuse collection** ("Haus- und Gewerbekehrichtabfuhr"): this is not published as a list of dates. It runs once a week, on a German weekday (e.g. `Dienstag`/Tuesday or `Mittwoch`/Wednesday) that depends on where in Muttenz an address is. Rather than hardcoding which weekday applies to which area, the source resolves the link to the *current* "Abfallkalender" PDF from a stable info page (`https://www.muttenz.ch/_rte/regelmaessigeranlass/855`) and parses that PDF on every run to discover which weekday(s) are currently valid and what area each one covers. You tell the source which weekday applies to your address via the `zone` parameter; the source re-validates that weekday against the live document every time it runs, so if the municipality ever changes the split, you get a clear error instead of silently wrong dates.
- **Town-wide special collections** (Papiersammlung, Grünabfuhr, Kunststoffsammlung, Altmetallabfuhr, Häckseltag, Sonderabfallsammlung, Weihnachtsbaumabfuhr, Umwelttag): these dates are the same for the whole municipality and are fetched live from `https://www.muttenz.ch/abfalldaten`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muttenz_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**
*(string) (required)*

The German weekday name of your regular refuse collection day (e.g. `Dienstag` or `Mittwoch`). This is validated against the current official Abfallkalender on every update, so only weekdays actually listed there for the current year will work.

## How to find your `zone`

Open the official ["Abfuhrdaten"](https://www.muttenz.ch/abfalldaten) page and follow the "Aktueller Abfallkalender" link to the current calendar PDF. Its "Abfuhr-Kurzinformationen" section lists the currently valid weekday(s) for "Haus- und Gewerbekehricht" and describes which part of Muttenz each one covers (at the time of writing, this is a simple split around Prattelerstrasse/St.-Jakob-Strasse, but the source does not assume this stays the same — always check the current document). Enter the weekday that matches your address as the `zone` value.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muttenz_ch
      args:
        zone: "Dienstag"
```

## Bin types returned

| Provider description  | Returned type          | Icon                    |
|------------------------|-------------------------|--------------------------|
| Haus-/Gewerbekehrichtabfuhr | Kehrichtabfuhr    | `mdi:trash-can`          |
| Papiersammlung          | Papiersammlung          | `mdi:package-variant`    |
| Grünabfuhr              | Grünabfuhr               | `mdi:flower`             |
| Kunststoffsammlung      | Kunststoffsammlung      | `mdi:recycle-variant`    |
| Altmetallabfuhr         | Altmetallabfuhr         | `mdi:nail`               |
| Häckseltag              | Häckseltag               | `mdi:flower`             |
| Sonderabfallsammlung    | Sonderabfallsammlung    | `mdi:biohazard`          |
| Weihnachtsbaumabfuhr    | Weihnachtsbaumabfuhr    | `mdi:pine-tree`          |
| Umwelttag               | Umwelttag                | `mdi:calendar`           |

Note: `Kehrichtabfuhr` entries include a `description` field with the area description currently published for the selected weekday in the official Abfallkalender.

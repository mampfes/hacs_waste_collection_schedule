# Reinach BL

Support for waste collection schedules provided by [Gemeinde Reinach BL](https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender), Switzerland.

The source consumes the official Reinach BL RSS feed:
`https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender/rss.php`

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: reinach_bl_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**
*(string) (required)*

The collection zone within Reinach BL. Must be one of:

- `Kreis Ost`
- `Kreis West`

## How to find your `zone`

Open the [official Reinach BL waste calendar](https://www.reinach-bl.ch/de/abfallwirtschaft/abfallkalender). The page shows the two collection zones (`Kreis Ost` and `Kreis West`) and indicates which streets belong to each zone.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: reinach_bl_ch
      args:
        zone: "Kreis Ost"
```

## Bin types returned

The RSS feed uses the German waste-type names listed below. Unknown types are still returned with no icon.

| Provider description | Returned type        | Icon                              |
|----------------------|----------------------|-----------------------------------|
| Hauskehricht         | Hauskehricht         | `mdi:trash-can`                   |
| Grünabfuhr/Bioabfall | Grünabfuhr/Bioabfall | `mdi:leaf`                        |
| Häckseldienst        | Häckseldienst        | `mdi:chainsaw`                    |
| Papier               | Papier               | `mdi:newspaper-variant-outline`   |
| Karton               | Karton               | `mdi:package-variant`             |
| Metalle              | Metalle              | `mdi:nail`                        |

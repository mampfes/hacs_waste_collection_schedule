# FL Abfalltransport AG

Support for schedules provided by [FL Abfalltransport AG](https://www.abfalltransport.li).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltransport_li
      args:
        municipality: MUNICIPALITY
        waste_type: WASTE_TYPE
```

### Configuration Variables

**municipality**  
*(string) (required)*

Name of the municipality in lower case. Supported values:
`balzers`, `triesen`, `triesenberg`, `vaduz`, `schaan`, `planken`, `gamprin-bendern`, `ruggell`, `mauren-schaanwald`, `eschen-nendeln`, `schellenberg`

**waste_type**  
*(string) (optional, default: `kehricht`)*

Type of waste collection. Supported values:
- `kehricht` — household waste (Kehricht)
- `gruenabfuhr` — green waste (Grünabfuhr)
- `all` — both waste types

## Examples

Household waste in Balzers:

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltransport_li
      args:
        municipality: balzers
        waste_type: kehricht
```

Green waste in Vaduz:

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltransport_li
      args:
        municipality: vaduz
        waste_type: gruenabfuhr
```

Both waste types in Schaan (single source entry):

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltransport_li
      args:
        municipality: schaan
        waste_type: all
```

## How to get the source arguments

Visit [https://www.abfalltransport.li/abfallkalender](https://www.abfalltransport.li/abfallkalender) and select your municipality and waste type to see your collection schedule.

Use the municipality name in lower case as the `municipality` argument (e.g. `balzers`, `vaduz`). For municipalities with a hyphen in their name, use the hyphenated form (e.g. `gamprin-bendern`, `mauren-schaanwald`, `eschen-nendeln`).

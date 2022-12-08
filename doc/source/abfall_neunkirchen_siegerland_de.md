# Neunkirchen Siegerland

Support for schedules provided by [Gemeinde Neunkirchen Siegerland](https://www.neunkirchen-siegerland.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_neunkirchen_siegerland_de
      args:
        strasse: STRASSE
```

### Configuration Variables

**searchterm**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_neunkirchen_siegerland_de
      args:
        strasse: "Bahnhofst*"

```

## How to get the source arguments

1. Go to your calendar at (https://www.neunkirchen-siegerland.de/Rathaus-Politik/B%C3%BCrgerservice/Abfalltermine/)
2. Enter your Streen.
3. Copy the exact values from the  textboxes streen in the source configuration. 

*IMPORTANT* - only streetname or part of streetname without ()
the string as strasse must match only 1 entry

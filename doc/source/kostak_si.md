# Kostak Krško

Support for schedules provided by [Kostak Krško](https://www.kostak.si).

Source for Kostak d.o.o. waste collection in Krško, Slovenia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kostak_si
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kostak_si
      args:
        address: "Senu\u0161e 3"
```

## How to get the source arguments

Search for your address at https://uod.kostak.si/ and enter it as street name, house number and optional house number suffix, for example 'Senuše 3' or 'Cesta krških žrtev 134A'.

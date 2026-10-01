# Gemeinde Ismaning – Abfallkalender

Support for schedules provided by [Gemeinde Ismaning – Abfallkalender](https://ismaning.de/umwelt-energie/abfall/abfallkalender/).

Source for the waste collection schedule of the community Ismaning, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ismaning_de
      args:
        street: STREET
        street_nr: STREET_NR
```

### Configuration Variables

**street**  
*(string) (required)*

**street_nr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ismaning_de
      args:
        street: Am Englischen Garten
```

## How to get the source arguments

Enter your street. If the street requires a house number, enter it as well (only needed for streets that are split into house-number ranges; leave empty otherwise).

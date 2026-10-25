# CoABSeR

Support for schedules provided by [CoABSeR](https://coabser.it).

Source for CoABSeR (Alba, Bra and Roero, Piedmont) household collection calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: coabser_it
      args:
        comune: COMUNE
```

### Configuration Variables

**comune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: coabser_it
      args:
        comune: Sommariva Perno
```

## How to get the source arguments

Enter your comune as listed on https://coabser.it/servizi/calendari-utenze-domestiche/, for example `Sommariva Perno`. Alba (no text layer) and Bra (one calendar per zone in a single PDF) are not supported.

# Timrå kommun

Support for schedules provided by [Timrå kommun](https://www.timra.se/), serving the municipality of Timrå, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: timra_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)* : Property address (Belägenhetsadress) as used by Timrå kommun, e.g. `"Aspen 195"`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: timra_se
      args:
        address: "Aspen 195"
```

## How to get the source argument

Enter the property address exactly as shown on the [Timrå kommun waste collection map](https://kartor.timra.se/portal/apps/experiencebuilder/experience/?id=186668f9efeb458c926d85a978fe85de), e.g. `"Aspen 195"`. If the address cannot be found, the error message will list similar addresses to help you find the correct spelling.

## Notes

Timrå kommun uses a "fyrfack" (four-compartment) collection system with two bins per property:

- **Fyrfackskärl 1** — collected roughly every 4 weeks.
- **Fyrfackskärl 2** — collected roughly every 2 weeks.

The exact waste fractions held in each bin are not exposed by the underlying data source, so both bins are reported using their generic names.

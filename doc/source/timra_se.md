# Timrå kommun

Support for schedules provided by [Timrå kommun](https://www.timra.se).

Source for Timrå kommun (Sweden) waste collection.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: timra_se
      args:
        address: Aspen 195
```

## How to get the source arguments

Enter the property address exactly as shown on the Timrå kommun waste collection map (Belägenhetsadress), e.g. 'Aspen 195'. You can look up the address at https://kartor.timra.se/portal/apps/experiencebuilder/experience/?id=186668f9efeb458c926d85a978fe85de

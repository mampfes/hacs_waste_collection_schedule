# Select'om

Support for schedules provided by [Select'om](https://www.select-om.com).

Source for the Select'om (Bas-Rhin) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: select_om_com
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: select_om_com
      args:
        commune: Molsheim
```

## How to get the source arguments

Enter your commune as listed on https://www.select-om.com/le-selectom-vous/calendrier-des-collectes/, for example `Molsheim`.

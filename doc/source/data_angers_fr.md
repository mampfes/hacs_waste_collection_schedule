# Angers Loire Métropole

Support for schedules provided by [Angers Loire Métropole](https://data.angers.fr/).

Source script for data.angers.fr

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_angers_fr
      args:
        typevoie: TYPEVOIE
        address: ADDRESS
        city: CITY
        num_voie: NUM_VOIE
```

### Configuration Variables

**typevoie**  
*(string) (required)*

**address**  
*(string) (required)*

**city**  
*(string) (required)*

**num_voie**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_angers_fr
      args:
        address: cerisiers
        city: TRELAZE
        typevoie: allee
```

## How to get the source arguments

Select your city and street type, then enter (part of) the street name. The house number is optional but needed when the street is split between several collection sectors.

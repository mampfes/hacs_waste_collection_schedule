# Västervik Miljö & Energi

Support for schedules provided by [Västervik Miljö & Energi](https://www.vmeab.se/), serving Västervik, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: vmeab_se
      args:
        city: CITY (ORT)
        street: STREET (GATUADRESS)
        
```

### Configuration Variables

**city**  
*(String) (required)*

**street**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: vmeab_se
      args:
        city: Odensvi
        street: Ringsfall 1
        
```

## How to get the source argument

Use your city and street. You can check here (<https://www.vmeab.se/tjanster/avfall--atervinning/min-sophamtning/>) if your arguments work.

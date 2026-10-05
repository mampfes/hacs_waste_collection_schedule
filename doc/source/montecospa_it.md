# Monteco Spa

Support for schedules provided by [Monteco Spa](https://www.montecospa.it).

Source for Monteco Spa waste collection (Puglia, Italy).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: montecospa_it
      args:
        municipality: MUNICIPALITY
        zone: ZONE
        user_type: USER_TYPE
```

### Configuration Variables

**municipality**  
*(string) (required)*

**zone**  
*(string) (required)*

**user_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: montecospa_it
      args:
        municipality: Lecce
        zone: zona_centro_storico
```

## How to get the source arguments

Visit https://www.montecospa.it/it/servizi-evoluti?cta=calendario , click your address on the map, and note the municipality (exactly as listed on the Monteco website, e.g. 'Lecce') and the zone shown in the results panel (e.g. 'zona_centro_storico'). The user type is 'Domestica' (default) or 'Non domestica'.

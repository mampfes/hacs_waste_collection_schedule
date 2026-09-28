# SiUnet

Support for schedules provided by [SiUnet](https://www.siunet.it).

Source for waste collection calendars published on the SiUnet platform (differenziati.siunet.it) by Greenext, serving municipalities across Italy under various local branded apps (e.g. Esacom).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: siunet_it
      args:
        comune: COMUNE
        zona: ZONA
```

### Configuration Variables

**comune**  
*(string) (required)*

**zona**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: siunet_it
      args:
        comune: ZEVIO
```

## How to get the source arguments

Use the municipality name exactly as listed below. Two entries with the same name that switched providers are disambiguated with a '(1)'/'(2)' suffix: try the other one if your municipality returns no results. If your municipality splits collections by zone, add the zone name from your local waste-management provider's calendar (e.g. 'Zona Rossa'); collections that are not zone-specific are always included.

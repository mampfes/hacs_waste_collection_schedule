# Grand Paris Sud Est Avenir (GPSEA)

Support for schedules provided by [Grand Paris Sud Est Avenir (GPSEA)](https://sudestavenir.fr/).

Source script for sudestavenir.fr, waste collection schedules for the Grand Paris Sud Est Avenir (GPSEA) intercommunal territory

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sudestavenir_fr
      args:
        commune: COMMUNE
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**commune**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sudestavenir_fr
      args:
        commune: Creteil
        street: Place du Grand Pavois
        house_number: '1'
```

## How to get the source arguments

Enter your GPSEA commune, street and house number. French street types such as Place/PL and Avenue/AV are accepted. The infosheet supplies recurring weekdays, date lists, seasons and morning/afternoon details. Dated precision belongs to the year of its published calendar link. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

# Abfallwirtschaft Rendsburg

Support for schedules provided by [Abfallwirtschaft Rendsburg](https://www.awr.de).

Source for Abfallwirtschaft Rendsburg

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awr_de
      args:
        city: CITY
        street: STREET
        waste_types: WASTE_TYPES
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**waste_types**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awr_de
      args:
        city: Rendsburg
        street: "Hindenburgstra\xDFe"
```

## How to get the source arguments

Enter city and street exactly as on https://www.awr.de/service/abfuhrtermine/. A street lists every container variant the city collects (e.g. Restabfall 2-weekly and 4-weekly). To get only your own bins, select them on the website and copy the ids from the calendar link, e.g. .../abfallarten/R02-B02-D04-P04/kalender.ics, into waste_types as R02,B02,D04,P04. Leave it empty to get every variant.

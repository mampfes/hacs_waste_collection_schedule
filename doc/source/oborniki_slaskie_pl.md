# Oborniki Śląskie

Support for schedules provided by [Oborniki Śląskie](https://www.alba.com.pl).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oborniki_slaskie_pl
      args:
        street: [Street name]
        waste_type: [Waste type]
```

### Configuration Variables

**street**  
*(string) (optional)*

The street name or district to filter schedules for. If not provided, all schedules will be returned.

**waste_type**  
*(string/array) (optional)*

The waste type(s) to filter for. If not provided or set to 'all', all waste types will be included.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: oborniki_slaskie_pl
      args:
        street: ul. Mickiewicza
        waste_type: Odpady zmieszane
```

## How to get the source arguments

The source fetches waste collection schedules from a PDF document published by Alba (the waste management provider for Oborniki Śląskie). 

- **street**: Provide the street name or district as it appears in the PDF schedule
- **waste_type**: Filter for specific waste types like "Odpady zmieszane", "Papier", etc.

The PDF URL is updated yearly (currently: https://www.alba.com.pl/download/2114.pdf). The source automatically extracts dates and waste types from the PDF table structure.

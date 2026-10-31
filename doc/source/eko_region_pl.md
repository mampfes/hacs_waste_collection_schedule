# EKO-REGION (Gmina Szczerców)

Support for schedules provided by [EKO-REGION (Gmina Szczerców)](https://eko-region.pl).

Source for residential waste collection in Gmina Szczerców's villages.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eko_region_pl
      args:
        village: VILLAGE
```

### Configuration Variables

**village**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eko_region_pl
      args:
        village: Szubienice
```

## How to get the source arguments

Find your village on https://eko-region.pl/gmina/szczercow/ and enter its name as printed there (for example Szubienice). The source automatically follows the Nieruchomości Zamieszkałe residential link. Business/non-residential schedules and Szczerców town's separate street calendars are not supported. Ash dates marked (popiół) in the Bio column are classified separately as Other, with the original Popiół label retained. Bulky-waste notices state multi-day windows covering different villages, so no exact bulky date is inferred.

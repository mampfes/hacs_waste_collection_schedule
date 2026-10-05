# PreZero Bielsko-Biała

Support for schedules provided by [PreZero Bielsko-Biała](https://prezero-bielsko.pl/harmonogram-odbioru-odpadow/).

Source for PreZero Bielsko-Biała waste collection schedule

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bielsko_pl
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: prezero_bielsko_pl
      args:
        street: Krakowska
        house_number: '12'
```

## How to get the source arguments

Enter your street and house number in Bielsko-Biała as they appear on https://prezero-bielsko.pl/harmonogram-odbioru-odpadow/.

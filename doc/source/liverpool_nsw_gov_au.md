# Liverpool City Council (NSW)

Support for schedules provided by [Liverpool City Council (NSW)](https://www.liverpool.nsw.gov.au/).

Source for Liverpool City Council (NSW, Australia)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: liverpool_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: liverpool_nsw_gov_au
      args:
        address: 600 Kurrajong Road, Carnes Hill, NSW 2171
```

## How to get the source arguments

Enter your address as listed in the Liverpool City Council open data set, e.g. '600 Kurrajong Road, Carnes Hill, NSW 2171'.

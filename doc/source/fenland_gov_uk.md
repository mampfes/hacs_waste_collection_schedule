# Fenland District Council

Support for schedules provided by [Fenland District Council](https://www.fenland.gov.uk/).

Source script for fenland.gov.uk services for Fenland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fenland_gov_uk
      args:
        post_code: POST_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**post_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fenland_gov_uk
      args:
        post_code: PE13 1JR
        house_number: Flat 1
```

## How to get the source arguments

Enter your postcode and the house number (or flat or house name) as it starts your address, e.g. `Flat 1` for `Flat 1 24 North Brink`.

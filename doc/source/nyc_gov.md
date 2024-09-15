# New York City

Support for schedules provided by [New York City](https://www.nyc.gov/assets/dsny/forms/collection-schedule), serving the city of New York, NY, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nyc_gov
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
    - name: nyc_gov
      args:
        address: Queens Borough Hall, 120-55 Queens Blvd, Jamaica, NY 11424, USA
```

## How to get the source argument

The `address` argument is simply the house mailing address. You can what formats of your address are accepted at <https://www.nyc.gov/assets/dsny/forms/collection-schedule>.

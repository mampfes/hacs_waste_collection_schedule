# Kansas City, MO

Support for schedules provided by [Kansas City, MO](https://www.kcmo.gov/city-hall/trash).

Source for Kansas City, Missouri trash and recycling collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kansas_city_mo_us
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
    - name: kansas_city_mo_us
      args:
        address: 4632 Paseo, Kansas City, MO 64110
```

## How to get the source arguments

Enter the full street address including city and state (e.g. '4632 Paseo, Kansas City, MO 64110').

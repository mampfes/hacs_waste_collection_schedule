# Republic Services

Support for schedules provided by [Republic Services](https://republicservices.com), serving the municipality all over the United States of America.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: "101 E Main St, Georgetown, KY 40324"
```

## How to check the street address

The street address can be tested [here](https://republicservices.com).
# Toronto (ON)

Support for schedules provided by [Toronto (ON)](https://www.toronto.ca).

Source for Toronto waste collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: toronto_ca
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
    - name: toronto_ca
      args:
        street_address: 224 Wallace Ave
```

## How to get the source arguments

Enter your street address as the City of Toronto writes it, for example '224 Wallace Ave'. The first match of the city's address search is used.

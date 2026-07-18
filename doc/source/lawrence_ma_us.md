# City of Lawrence

Support for schedules provided by [City of Lawrence](https://www.cityoflawrence.com).

Source for City of Lawrence, Massachusetts, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lawrence_ma_us
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lawrence_ma_us
      args:
        street: Adams Street
```

## How to get the source arguments

Open the City of Lawrence collection schedule at https://www.cityoflawrence.com/161/Collection-Schedule and find your street on the Monday to Friday tabs. Enter the street name exactly as listed (for example 'Adams Street'). Omit any segment qualifier shown in brackets.

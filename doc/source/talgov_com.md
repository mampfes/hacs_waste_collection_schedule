# City of Tallahassee

Support for schedules provided by [City of Tallahassee](https://www.talgov.com/you/swslookup).

Source for City of Tallahassee, FL waste, recycling and bulky item/yard waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: talgov_com
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
    - name: talgov_com
      args:
        address: 400 S Monroe St
```

## How to get the source arguments

Enter the street address as shown in the City of Tallahassee [solid waste lookup](https://www.talgov.com/you/swslookup), e.g. '400 S Monroe St'.

# Phoenix, AZ

Support for schedules provided by [Phoenix, AZ](https://www.phoenix.gov/publicworks/garbage/trashschedule/find-your-day-of-collection).

Source for City of Phoenix, AZ trash and recycling collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: phoenix_gov
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
    - name: phoenix_gov
      args:
        address: 4750 S 48th St, Phoenix, AZ 85040
```

## How to get the source arguments

Enter the full street address including city and state (e.g. '4750 S 48th St, Phoenix, AZ 85040').

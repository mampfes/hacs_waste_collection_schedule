# City of Tallahassee

Support for schedules provided by [City of Tallahassee, FL](https://www.talgov.com/you/swslookup), covering weekly garbage/recycling collection and the biweekly Red/Blue Bulky Items/Yard Waste collection.

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

Visit the [Waste Management Pick Up Schedule lookup](https://www.talgov.com/you/swslookup) page, start typing your address in the "Enter an Address" field, and pick your address from the autocomplete list. Use the address exactly as it appears in that list (e.g. `400 S Monroe St`).

# Marysville, WA

Support for schedules provided by [Marysville, WA](https://marysvillewa.gov/172/Solid-Waste-Recycling).

Source for Marysville, WA solid waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: marysville_wa_us
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
    - name: marysville_wa_us
      args:
        street_address: 501 Delta Ave
```

## How to get the source arguments

Enter the house number and street name (e.g. '501 Delta Ave' or '6400 88th St NE'), without city or ZIP code.

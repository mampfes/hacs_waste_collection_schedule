# Bundaberg Regional Council

Support for schedules provided by [Bundaberg Regional Council](https://www.bundaberg.qld.gov.au).

Source for Bundaberg Regional Council, QLD, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bundaberg_qld_gov_au
      args:
        street_number: STREET_NUMBER
        street_name: STREET_NAME
        suburb: SUBURB
```

### Configuration Variables

**street_number**  
*(string) (required)*

**street_name**  
*(string) (required)*

**suburb**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bundaberg_qld_gov_au
      args:
        street_number: '10'
        street_name: Maynard
        suburb: AVENELL HEIGHTS
```

## How to get the source arguments

Enter the street number and street name (without the street type, e.g. 'Maynard' for Maynard Street), and the suburb in capitals, e.g. 'AVENELL HEIGHTS'. Without a suburb the first matching address is used. General waste is collected weekly and recycling fortnightly.

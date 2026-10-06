# Lincoln, CA

Support for schedules provided by [Lincoln, CA](https://www.lincolnca.gov/recycling).

Source for City of Lincoln, California (Placer County) garbage and green waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lincoln_ca_us
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
    - name: lincoln_ca_us
      args:
        street_address: 671 East Avenue
```

## How to get the source arguments

Enter the house number and street (e.g. '671 East Avenue' or '671 East Ave'); city and ZIP are optional. Directions are stored as N/E/S/W. You can check your collection day and green waste colour on the City's Garbage Schedule map at https://www.lincolnca.gov/recycling.

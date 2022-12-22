# Maribyrnong Council (VIC)

Support for schedules provided by [Maribyrnong Council (VIC)](https://www.maribyrnong.vic.gov.au/Residents/Bins-and-recycling).
Note: Case Sensitive!

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maribyrnong
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**street_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maribyrnong
      args:
        suburb: Footscray
        street_name: Ballarat Rd
        street_number: 70-100
```

## How to get the source arguments

Visit the [Maribyrnong Council (VIC)](https://www.maribyrnong.vic.gov.au/Residents/Bins-and-recycling) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property.

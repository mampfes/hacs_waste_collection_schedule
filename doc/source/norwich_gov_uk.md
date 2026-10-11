# Norwich City Council

Support for schedules provided by [Norwich City Council](https://www.norwich.gov.uk/bins-and-recycling).

Source for Norwich City Council bin collection via Whitespace BNR platform

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: norwich_gov_uk
      args:
        property_name_or_number: PROPERTY_NAME_OR_NUMBER
        street_name: STREET_NAME
        postcode: POSTCODE
```

### Configuration Variables

**property_name_or_number**  
*(string) (required)*

**street_name**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: norwich_gov_uk
      args:
        property_name_or_number: '33'
        street_name: Carrow Road
        postcode: NR1 1HS
```

## How to get the source arguments

Provide the house name or number, the street and the postcode as shown on the council's bin-day lookup.

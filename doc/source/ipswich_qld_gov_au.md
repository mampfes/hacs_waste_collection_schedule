# Ipswich City Council

Support for schedules provided by [Ipswich City Council](https://www.ipswich.qld.gov.au/live/waste-and-recycling/bin-collection-calendar).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_qld_gov_au
      args:
        street: STREET_NO_NAME_TYPE
        suburb: SUBURB
```

### Configuration Variables

**street**  
*(string) (required)*

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_qld_gov_au
      args:
        street: 50 Brisbane Road
        suburb: Redbank
```

## How to get the source arguments

Visit the [Ipswich City Council bin collection calendar](https://www.ipswich.qld.gov.au/live/waste-and-recycling/bin-collection-calendar) page and search for your address. Use your street number and name (include type such as street, avenue, road) for street and suburb only name in suburb. Including QLD or Australia is not required.

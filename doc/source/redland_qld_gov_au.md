# Redland City Council (QLD)

Support for schedules provided by [Redland City Council (QLD)](https://www.redland.qld.gov.au/info/20188/bins_and_collections/781/bin_collection_day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: redland_qld_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: redland_qld_gov_au
      args:
        suburb: Redland Bay
        street_name: Boundary Street
        street_number: 1
```

## How to get the source arguments

Visit the [Redland City Council (QLD)](https://www.redland.qld.gov.au/info/20188/bins_and_collections/781/bin_collection_day) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property.
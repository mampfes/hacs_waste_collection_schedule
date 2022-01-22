# Brisbane City Council

Support for schedules provided by [Brisbane City Council](https://www.brisbane.qld.gov.au/clean-and-green/rubbish-tips-and-bins/rubbish-collections/bin-collection-calendar).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: brisbane_qld_gov_au
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
    - name: brisbane_qld_gov_au
      args:
        suburb: Milton
        street_name: Park Rd
        street_number: 8/1
```

## How to get the source arguments

Visit the [Brisbane City Council bin collection calendar](https://www.brisbane.qld.gov.au/clean-and-green/rubbish-tips-and-bins/rubbish-collections/bin-collection-calendar) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property.

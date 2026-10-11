# West Oxfordshire District Council

Support for schedules provided by [West Oxfordshire District Council](https://westoxon.gov.uk/).

Source for West Oxfordshire District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westoxon_gov_uk
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
    - name: westoxon_gov_uk
      args:
        address: 75 manor road woodstock, ox20 1xr
```

## How to get the source arguments

Go to the West Oxfordshire waste collection enquiry page (https://community.westoxon.gov.uk/s/waste-collection-enquiry) and type your postcode or street name into the address lookup. Use the full address string exactly as it is returned by the autocomplete.

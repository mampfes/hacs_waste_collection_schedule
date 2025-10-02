# South Staffordshire Council

Support for schedules provided by [South Staffordshire Council](https://www.sstaffs.gov.uk/bins-and-recycling/view-your-collection-calendar), serving South Staffordshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sstaffs_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables
**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sstaffs_gov_uk
      args:
        uprn: "100031831923"
```

## How to find your `UPRN`

Your UPRN is displayed in the url when you are looking at your collection schedule. For example: _sstaffs.gov.uk/where-i-live?uprn=`100031831923`_

Alternatively, an easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
`

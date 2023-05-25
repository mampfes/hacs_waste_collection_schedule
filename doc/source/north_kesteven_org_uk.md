# North Kesteven District Council

Support for schedules provided by [North Kesteven District Council](https://www.n-kesteven.org.uk/bins), serving North Kesteven, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: n-kesteven_org_uk
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
    - name: n-kesteven_org_uk
      args:
        uprn: "100030866950"
```

## How to find your `UPRN`

The easiest way to find your Unique Property Reference Number (UPRN) is to search for your bin collection schedule on the n-kesteve.org.uk website. Your uprn is the collection of digits at the end of the url, and is also shown under the `Bookmarkable link` section.

For example: www.n-kesteven.org.uk/bins/display?uprn=`100030866950
`
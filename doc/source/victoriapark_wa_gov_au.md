# Town of Victoria Park Council

Support for schedules provided by [Town of Victoria Park Bins and collections](https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: victoriapark_wa_gov_au
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
    - name: victoriapark_wa_gov_au
      args:
        address: 99 Shepperton Road East Victoria Park 6101
```

## How to get the source arguments

Visit the [Town of Victoria Park Bins and collections](https://www.victoriapark.wa.gov.au/residents/waste-and-recycling/bins-and-collections.aspx) page and search for your address. The arguments should exactly match the results of the property.

Currently exporting out:

 - Rubbish
 - Recycling
 - Go Bin
 - Green Waste
 - Bulk Waste
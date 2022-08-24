# Manchester City Council

Support for schedules provided by [Manchester City
Council](https://www.manchester.gov.uk/bincollections/), serving the
city of Manchester, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: manchester_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: manchester_uk
      args:
        uprn: "100031540175"
```

## How to get the source argument

The UPRN code can be found in the page by entering your postcode on the
[Manchester City Council Bin Collections page
](https://www.manchester.gov.uk/bincollections/).  When on the address list, 
View the source code for the page, and look for your address, the uprn will be
shown as the value.

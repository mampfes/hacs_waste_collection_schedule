# Aylesbury Vale District Council

Support for schedules provided by [Aylesbury Vale District Council](https://account.aylesburyvaledc.gov.uk/resident2/s/guest-flow-form?service_ref=DSHLC_AVDC_Find_Bin_Days), serving Aylesbury Vale, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: aylesburyvaledc.gov.uk
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
    - name: aylesburyvaledc.gov.uk
      args:
        uprn: "766292368"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
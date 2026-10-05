# Welwyn Hatfield Borough Council

Support for schedules provided by [Welwyn Hatfield Borough Council](https://www.welhat.gov.uk).

Source for www.welhat.gov.uk services for Welwyn Hatfield Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: welhat_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: welhat_gov_uk
      args:
        uprn: '100080965745'
        postcode: AL9 5EA
```

## How to get the source arguments

Go to https://www.welhat.gov.uk/xfp/form/214 and enter your postcode. The UPRN is the option value of your address in the address dropdown (browser dev tools); you can also look it up on https://www.findmyaddress.co.uk/.

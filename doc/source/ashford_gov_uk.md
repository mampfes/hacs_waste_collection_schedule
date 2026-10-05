# Ashford Borough Council

Support for schedules provided by [Ashford Borough Council](https://ashford.gov.uk).

Source for Ashford Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ashford_gov_uk
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
    - name: ashford_gov_uk
      args:
        uprn: 100060796052
        postcode: TN23 3DY
```

## How to get the source arguments

Enter your postcode and the UPRN of your property. You can find your UPRN at https://www.findmyaddress.co.uk/.

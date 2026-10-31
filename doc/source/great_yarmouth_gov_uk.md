# Great Yarmouth Borough Council

Support for schedules provided by [Great Yarmouth Borough Council](https://myaccount.great-yarmouth.gov.uk).

Source for waste collection services for Great Yarmouth Borough Council, Norfolk, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: great_yarmouth_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: great_yarmouth_gov_uk
      args:
        uprn: '100090834016'
```

## How to get the source arguments

Enter the Unique Property Reference Number (UPRN) of your property. You can find it at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names, and the dates a bulky collection can be booked are no longer listed as collections. Update filters, automations and customisations using the old labels.

# Great Yarmouth Borough Council

Support for schedules provided by [Great Yarmouth Borough Council](https://myaccount.great-yarmouth.gov.uk), serving the Borough of Great Yarmouth, Norfolk, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Norfolk, please continue to use the source for your current area as long as it's still working. New sources for the new East Norfolk council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: great_yarmouth_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN). An easy way to find this is by visiting [findmyaddress.co.uk](https://www.findmyaddress.co.uk/) and entering your address details.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: great_yarmouth_gov_uk
      args:
        uprn: "100090834016"
```

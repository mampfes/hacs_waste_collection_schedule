# Borough Council of King's Lynn & West Norfolk

Support for schedules provided by [Borough Council of King's Lynn & West Norfolk](https://www.west-norfolk.gov.uk), serving the Borough of King's Lynn & West Norfolk, UK.

## Local Government Reorganisation note
This source **only** serves the areas covered by the **existing** King's Lynn & West Norfolk Council, and not the upcoming West Norfolk Council.

During the ongoing local government reorganisation (LGR) in Norfolk, please continue to use the source for your current area as long as it's still working. New sources for the new West Norfolk council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: west_norfolk_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: west_norfolk_gov_uk
      args:
        uprn: "100090989776"
```

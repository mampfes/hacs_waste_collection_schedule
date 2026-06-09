# Rushmoor Borough Council

Support for schedules provided by [Rushmoor Borough Council](https://www.rushmoor.gov.uk/recycling-rubbish-and-environment/bins-and-recycling/bin-collection-day-finder/), serving Rushmoor, Hampshire, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new North Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rushmoor_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rushmoor_gov_uk
      args:
        uprn: "100060551749"
```

## How to get the source argument

Find the UPRN of your address using [https://www.findmyaddress.co.uk/search](https://www.findmyaddress.co.uk/search).

# Reigate & Banstead Borough Council

Support for schedules provided by the [Reigate & Banstead Borough](https://my.reigate-banstead.gov.uk/en/service/Bins_and_recycling___collections_calendar), serving the Reigate & Banstead Borough, Surrey, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Surrey, please continue to use the source for your current area as long as it's still working. New sources for the new East Surrey Council are not expected to be live until at least April 2027, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: reigatebanstead_gov_uk
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
    - name: reigatebanstead_gov_uk
      args:
        uprn: "68110755"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

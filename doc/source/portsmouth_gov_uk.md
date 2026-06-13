# Portsmouth City Council

Support for schedules provided by [Portsmouth City Council](https://www.portsmouth.gov.uk/), serving Portsmouth, Hampshire, UK.

If collection data is available for the address provided, it will return rubbish and recycling waste collection dates.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new South East Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: portsmouth_gov_uk
      args:
        uprn:     UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: portsmouth_gov_uk
      args:
        uprn: 1775027540
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.

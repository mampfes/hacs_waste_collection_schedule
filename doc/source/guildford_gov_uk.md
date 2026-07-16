# Guildford Borough Council

Support for schedules provided by [Guildford Borough Council](https://my.guildford.gov.uk/customers/s/view-bin-collections), serving Guildford, Surrey, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Surrey, please continue to use the source for your current area as long as it's still working. New sources for the new West Surrey Council are not expected to be live until at least April 2027, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: guildford_gov_uk
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
    - name: guildford_gov_uk
      args:
        uprn: "10007060305"
```

## How to get the source argument

Find the UPRN of your address using [https://www.findmyaddress.co.uk/search](https://www.findmyaddress.co.uk/search).

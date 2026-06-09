# Hart District Council

Support for schedules provided by [Hart District Council](https://www.hart.gov.uk/waste-and-recycling/when-my-bin-day), serving Hart, Hampshire, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new North Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hart_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: hart_gov_uk
      args:
        uprn: 100060420702
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.
Residential Addresses only. Some flat blocks are managed by trade waste companies.
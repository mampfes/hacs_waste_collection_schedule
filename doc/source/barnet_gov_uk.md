# London Borough of Barnet

Support for schedules provided by the [London Borough of Barnet](https://myforms.barnet.gov.uk/homepage/11/find-your-bin-collection-day), serving Barnet, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: barnet_gov_uk
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
    - name: barnet_gov_uk
      args:
        uprn: "200062903"
```

## How to get the source argument

An easy way of finding your UPRN is by going to [FindMyAddress service](https://www.findmyaddress.co.uk/) and entering in your address details.
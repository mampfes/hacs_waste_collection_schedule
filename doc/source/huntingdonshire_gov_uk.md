# Huntingdonshire District Council

Support for schedules provided by [Huntingdonshire District Council](https://www.huntingdonshire.gov.uk/refuse-calendar), serving Huntingdonshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: huntingdonshire_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: huntingdonshire_gov_uk
      args:
        uprn: "100050580641"
```

## How to get the source argument

The UPRN code can be found in the network request when entering your postcode and selecting your address on the [Huntingdonshire Waste Collection Calendar page](https://www.huntingdonshire.gov.uk/refuse-calendar/). You should look for a request like `https://www.huntingdonshire.gov.uk/refuse-calendar/100090123510` the last segment is your UPRN code.

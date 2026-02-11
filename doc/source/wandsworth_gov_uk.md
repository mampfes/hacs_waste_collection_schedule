# Wandsworth Council

Support for schedules provided by [Wandsworth Council](https://www.wandsworth.gov.uk/my-property/) for the London Borough of Wandsworth, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wandsworth_gov_uk
      args:
        uprn: "UPRN"
```

### Configuration Variables

**uprn**  
_(String | Integer) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wandsworth_gov_uk
      args:
        uprn: "100022659217"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk) and entering your address details.

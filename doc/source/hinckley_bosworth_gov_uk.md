# Hinckley & Bosworth Borough Council

Support for schedules provided by [Hinckley & Bosworth Borough Council](https://www.hinckley-bosworth.gov.uk/), serving Hinckley & Bosworth, Leicestershire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hinckley_bosworth_gov_uk
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
    - name: hinckley_bosworth_gov_uk
      args:
        uprn: "100030499851"
```

## How to get the source argument

Get your Unique Property Reference Number (UPRN) by going to <https://www.findmyaddress.co.uk/> and entering your address details.

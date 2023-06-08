# Maidstone Borough Council

Support for schedules provided by [Maidstone Borough Council](https://self.maidstone.gov.uk/service/check_your_bin_day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maidstone_gov_uk
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
    - name: maidstone_gov_uk
      args:
        uprn: "10014313638"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.

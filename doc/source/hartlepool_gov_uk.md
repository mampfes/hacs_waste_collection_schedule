# Hartlepool Borough Council

Support for schedules provided by [Hartlepool Borough Council](https://online.hartlepool.gov.uk/service/Refuse_and_recycling___check_bin_day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hartlepool_gov_uk
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
    - name: hartlepool_gov_uk
      args:
        uprn: "10009716952"
```

## How to get the source argument

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

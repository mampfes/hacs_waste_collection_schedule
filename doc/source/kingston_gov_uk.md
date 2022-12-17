#  Thr Royal Borough of Kingston Council

Support for schedules provided by [The Royal Borough of Kingston Council](https://kingston-self.achieveservice.com/service/in_my_area?displaymode=collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kingston_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: kingston_gov_uk
      args:
        uprn: "100110140843"
```

## How to get the source argument

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
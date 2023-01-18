# FCC Environment

Consolidated support for schedules provided by ~60 local authorities. Currently supports:
    - [Harborough District Council](https://www.harborough.gov.uk/)
    - [South Hams](https://southhams.gov.uk/)
    - [West Devon](https://www.westdevon.gov.uk/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fccenvironment_co_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        region: REGION_NAME
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

**region**<br>
*(string) (optional)*

Defaults to `harborough`, should be one of:
    - `harborough`
    - `westdevon`
    - `southhams`


## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: fccenvironment_co_uk
      args:
        uprn: 100030493289
```

## Example using UPRN and Region

```yaml
waste_collection_schedule:
    sources:
    - name: fccenvironment_co_uk
      args:
        uprn: 10001326041
        region: westdevon
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

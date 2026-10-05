# Telford and Wrekin Council

Support for schedules provided by [Telford and Wrekin Council](https://www.telford.gov.uk).

Source for telford.gov.uk, Telford and Wrekin Council, UK

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: telford_gov_uk
      args:
        uprn: UPRN
```

### Using post_code and name_number

```yaml
waste_collection_schedule:
  sources:
    - name: telford_gov_uk
      args:
        post_code: POST_CODE
        name_number: NAME_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**post_code**  
*(string) (alternative)*

**name_number**  
*(string) (alternative)*

Provide one of: `uprn` or `post_code` + `name_number`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: telford_gov_uk
      args:
        uprn: 000452097493
```

### Using post_code and name_number

```yaml
waste_collection_schedule:
  sources:
    - name: telford_gov_uk
      args:
        post_code: TF3 2DA
        name_number: '126'
```

## How to get the source arguments

Enter either your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your postcode and the house name or number exactly as the council lists it (e.g. '126').

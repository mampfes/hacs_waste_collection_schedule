# Ashfield District Council

Support for schedules provided by [Ashfield District Council](https://www.ashfield.gov.uk).

Source for ashfield.gov.uk, Ashfield District Council, UK

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: ashfield_gov_uk
      args:
        uprn: UPRN
```

### Using post_code and number

```yaml
waste_collection_schedule:
  sources:
    - name: ashfield_gov_uk
      args:
        post_code: POST_CODE
        number: NUMBER
```

### Using post_code and name

```yaml
waste_collection_schedule:
  sources:
    - name: ashfield_gov_uk
      args:
        post_code: POST_CODE
        name: NAME
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**post_code**  
*(string) (alternative)*

**number**  
*(string) (alternative)*

**name**  
*(string) (alternative)*

Provide one of: `uprn` or `post_code` + `number` or `post_code` + `name`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: ashfield_gov_uk
      args:
        uprn: 10001336299
```

### Using post_code and number

```yaml
waste_collection_schedule:
  sources:
    - name: ashfield_gov_uk
      args:
        post_code: NG17 9BH
        number: '1'
```

### Using post_code and name

```yaml
waste_collection_schedule:
  sources:
    - name: ashfield_gov_uk
      args:
        post_code: NG178ZA
        name: COUNCIL OFFICES
```

## How to get the source arguments

Enter either your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your postcode and either your house number (`number`) or your building name (`name`).

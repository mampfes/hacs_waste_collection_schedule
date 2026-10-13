# Cornwall Council

Support for schedules provided by [Cornwall Council](https://cornwall.gov.uk).

Source for cornwall.gov.uk services for Cornwall Council

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: cornwall_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and housenumberorname

```yaml
waste_collection_schedule:
  sources:
    - name: cornwall_gov_uk
      args:
        postcode: POSTCODE
        housenumberorname: HOUSENUMBERORNAME
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**housenumberorname**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `housenumberorname`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: cornwall_gov_uk
      args:
        uprn: '100040118005'
```

### Using postcode and housenumberorname

```yaml
waste_collection_schedule:
  sources:
    - name: cornwall_gov_uk
      args:
        postcode: TR261SP
        housenumberorname: '7'
```

## How to get the source arguments

Provide your UPRN, or provide both your postcode and house name or number. Find your UPRN at https://www.findmyaddress.co.uk/

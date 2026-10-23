# West Berkshire Council

Support for schedules provided by [West Berkshire Council](https://westberks.gov.uk).

Source for westberks.gov.uk services for West Berkshire Council

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: westberks_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and housenumberorname

```yaml
waste_collection_schedule:
  sources:
    - name: westberks_gov_uk
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
    - name: westberks_gov_uk
      args:
        uprn: '100080241094'
```

### Using postcode and housenumberorname

```yaml
waste_collection_schedule:
  sources:
    - name: westberks_gov_uk
      args:
        postcode: RG7 6NZ
        housenumberorname: PARROG HOUSE
```

## How to get the source arguments

Provide your UPRN, or your postcode plus your house name or number. Find your UPRN at https://www.findmyaddress.co.uk/

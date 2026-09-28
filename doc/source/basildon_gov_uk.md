# Basildon Council

Support for schedules provided by [Basildon Council](https://basildon.gov.uk).

Source for basildon.gov.uk services for Basildon Council, UK.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: basildon_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: basildon_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `address`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: basildon_gov_uk
      args:
        uprn: '100090277795'
```

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: basildon_gov_uk
      args:
        postcode: CM111BJ
        address: 6, HEADLEY ROAD
```

## How to get the source arguments

Provide your UPRN, or your postcode and the first line of your address as the council lists it, e.g. '6, HEADLEY ROAD'. Find your UPRN at https://www.findmyaddress.co.uk/

# Greater Cambridge Waste, UK

Support for schedules provided by [Greater Cambridge Waste, UK](https://greatercambridgewaste.org).

Source for greatercambridgewaste.org, the shared recycling and waste service for Cambridge City Council and South Cambridgeshire District Council.

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: greater_cambridge_waste_org
      args:
        uprn: UPRN
```

### Using postcode and name_or_number

```yaml
waste_collection_schedule:
  sources:
    - name: greater_cambridge_waste_org
      args:
        postcode: POSTCODE
        name_or_number: NAME_OR_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**name_or_number**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `name_or_number`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: greater_cambridge_waste_org
      args:
        uprn: 200004170895
```

### Using postcode and name_or_number

```yaml
waste_collection_schedule:
  sources:
    - name: greater_cambridge_waste_org
      args:
        postcode: CB13JD
        name_or_number: 37
```

## How to get the source arguments

Provide your UPRN, or your postcode together with your house name or number. Find your UPRN at https://www.findmyaddress.co.uk/

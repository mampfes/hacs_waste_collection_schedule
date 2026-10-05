# Bury Council

Support for schedules provided by [Bury Council](https://bury.gov.uk).

Source for bury.gov.uk services for Bury Council, UK.

## Configuration via configuration.yaml

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: bury_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Using id

```yaml
waste_collection_schedule:
  sources:
    - name: bury_gov_uk
      args:
        id: ID
```

### Configuration Variables

**postcode**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

**id**  
*(string) (alternative)*

Provide one of: `postcode` + `address` or `id`.

## Example

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: bury_gov_uk
      args:
        postcode: bl81dd
        address: 2 Oakwood Close
```

### Using id

```yaml
waste_collection_schedule:
  sources:
    - name: bury_gov_uk
      args:
        id: 649158
```

## How to get the source arguments

Enter your postcode and the first line of your address as listed on https://bury.gov.uk. Alternatively enter the property id: it is the `id` of your address in the response of https://www.bury.gov.uk/app-services/getProperties?postcode=<postcode>.

# Cotswold District Council

Support for schedules provided by [Cotswold District Council](https://www.cotswold.gov.uk/).

Source for Cotswold District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cotswold_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cotswold_gov_uk
      args:
        address: PARSONS PIECE, 1 GLEBE LANE, KEMBLE, CIRENCESTER, GL7 6BD
```

## How to get the source arguments

Go to the Cotswold District Council waste collection enquiry page (https://community.cotswold.gov.uk/s/waste-collection-enquiry) and start typing your postcode or street name into the address lookup. Select your property from the autocomplete suggestions and use the full address string exactly as it appears (e.g. '10 HAVEN HILL, CIRENCESTER, GL7 1BN').

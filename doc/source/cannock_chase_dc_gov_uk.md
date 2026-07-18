# Cannock Chase Council

Support for schedules provided by [Cannock Chase Council](https://www.cannockchasedc.gov.uk).

Source for cannockchasedc.gov.uk services for Cannock Chase Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cannock_chase_dc_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cannock_chase_dc_gov_uk
      args:
        uprn: '100031640287'
        postcode: WS15 1DN
```

## How to get the source arguments

Find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details, then provide it together with your postcode.

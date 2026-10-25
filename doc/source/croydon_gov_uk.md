# Croydon Council

Support for schedules provided by [Croydon Council](https://croydon.gov.uk).

Source for croydon.gov.uk services for Croydon Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: croydon_gov_uk
      args:
        postcode: POSTCODE
        houseID: HOUSEID
```

### Configuration Variables

**postcode**  
*(string) (required)*

**houseID**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: croydon_gov_uk
      args:
        postcode: CR0 6LN
        houseID: 64 Coniston Road
```

## How to get the source arguments

Enter your postcode and address as shown at https://service.croydon.gov.uk/wasteservices/w/webpage/bin-day-enter-address. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

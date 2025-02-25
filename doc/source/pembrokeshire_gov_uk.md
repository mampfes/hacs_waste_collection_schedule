# Pembrokeshire County Council

Bin collection schedules provided by [Pembrokeshire County Council](https://www.pembrokeshire.gov.uk/) in Wales, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: pembrokeshire_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**UPRN**  
*(string)(required)*

The "Unique Property Reference Number" for your address. You can find it by searching for your address at https://www.findmyaddress.co.uk/.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: pembrokeshire_gov_uk
      args:
        uprn: "100100283349"
```

## Returned collection types

### Food

Green Caddy for food recycling

### Paper

Blue Box for paper recycling 

### Glass

Green box for glass recycling

### Cardboard

Blue Bag for cardboard recycling

### Plastics

Red Bag for plastics recycling

### Non-Recyclables

Black/Grey Bags for non-recyclable waste

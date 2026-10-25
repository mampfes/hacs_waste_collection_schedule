# Broadland District Council

Support for schedules provided by [Broadland District Council](https://area.southnorfolkandbroadland.gov.uk/).

Source for southnorfolkandbroadland.gov.uk services for South Norfolk and Broadland, UK

## Configuration via configuration.yaml

### Using address_payload

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        address_payload: ADDRESS_PAYLOAD
```

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**address_payload**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

Provide one of: `address_payload` or `postcode` + `address`.

## Example

### Using address_payload

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        address_payload:
          Uprn: '010014355477'
          Address: 29 Mallard Way, Sprowston, Norwich, Norfolk, NR7 8DN
          X: '626227.00000'
          Y: '312136.00000'
          Ward: Sprowston East
          Parish: Sprowston
          Village: Sprowston
          Street: Mallard Way
          Authority: '2610'
```

### Using postcode and address

```yaml
waste_collection_schedule:
  sources:
    - name: south_norfolk_and_broadland_gov_uk
      args:
        postcode: NR7 8DN
        address: 29 Mallard Way, Sprowston, Norfolk, NR7 8DN
```

## How to get the source arguments

Enter the postcode and address from My Area, or supply the address_payload object from its MyArea.Data cookie. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.

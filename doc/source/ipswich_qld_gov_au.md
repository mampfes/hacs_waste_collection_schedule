# Ipswich City Council

Support for schedules provided by [Ipswich City Council](https://www.ipswich.qld.gov.au).

Source for Ipswich City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_qld_gov_au
      args:
        street: STREET
        suburb: SUBURB
        post_code: POST_CODE
```

### Configuration Variables

**street**  
*(string) (required)*

**suburb**  
*(string) (required)*

**post_code**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_qld_gov_au
      args:
        street: 184-202 Old Logan Rd
        suburb: Camira
        post_code: '4300'
```

## How to get the source arguments

Use your street number and street name (including the street type, e.g. Road, Street, Avenue) for street, and the suburb name only for suburb. Do not add QLD or Australia. Adding your post code is optional but recommended: it skips the council app's own address search, which is shared between all of its users and is regularly out of quota.

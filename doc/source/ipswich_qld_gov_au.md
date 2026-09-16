# Ipswich City Council

Support for schedules provided by [Ipswich City Council](https://www.ipswich.qld.gov.au/live/waste-and-recycling/bin-collection-calendar).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_qld_gov_au
      args:
        street: STREET_NO_NAME_TYPE
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
        street: 50 Brisbane Road
        suburb: Redbank
        post_code: "4301"
```

## How to get the source arguments

Visit the [Ipswich City Council bin collection calendar](https://www.ipswich.qld.gov.au/live/waste-and-recycling/bin-collection-calendar) page and search for your address. Use your street number and name (include type such as street, avenue, road) for street and suburb only name in suburb. Including QLD or Australia is not required.

Adding `post_code` is optional but recommended. With it, the address is sent to the council straight away. Without it, the address is first resolved through the search in the council's own app, which every user of that app shares and which is regularly out of its daily quota; while it is, lookups that omit `post_code` cannot run.

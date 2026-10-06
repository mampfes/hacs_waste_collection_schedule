# Oadby and Wigston Council

Support for schedules provided by [Oadby and Wigston Council](https://www.oadby-wigston.gov.uk).

Source for Oadby and Wigston Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oadby_wigston_gov_uk
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
    - name: oadby_wigston_gov_uk
      args:
        address: 56, Sussex Road, Wigston, Leicestershire
```

## How to get the source arguments

Enter the address exactly as the address search on [my.oadby-wigston.gov.uk](https://my.oadby-wigston.gov.uk/my-property-finder) suggests it, e.g. `56, Sussex Road, Wigston, Leicestershire`.

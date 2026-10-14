# City of Joondalup

Support for schedules provided by [City of Joondalup](https://www.joondalup.wa.gov.au).

Source for City of Joondalup (WA) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: joondalup_wa_gov_au
      args:
        number: NUMBER
        street: STREET
        suburb: SUBURB
        mapkey: MAPKEY
```

### Configuration Variables

**number**  
*(string) (optional)*

**street**  
*(string) (optional)*

**suburb**  
*(string) (optional)*

**mapkey**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: joondalup_wa_gov_au
      args:
        number: '2'
        street: Ashburton Drive
        suburb: Heathridge
```

## How to get the source arguments

Your house number, street name, and suburb as they appear when searching for your collection schedule on the Joonalup website: https://www.joondalup.wa.gov.au/residents/waste-and-recycling/residential-bin-collections. Alternatively, you can use your mapkey, if you know it.

# City of Joondalup

Support for schedules provided by [City of Joonalup](https://www.joondalup.wa.gov.au/residents/waste-and-recycling/residential-bin-collections).

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

Your house number as it appears on the Joondalup website.

**street**  
*(string) (optional)*

Your street name as it appears on the Joondalup website.

**suburb**  
*(string) (optional)*

Your suburb as it appears on the Joondalup website.

**mapkey**  
*(string) (optional)*

The unique identifier for your property used by the Joondalup website.


## Example

Your must provide either:
 - the number, street and suburb, or
 - the mapkey

The following examples are equivalent

```yaml
waste_collection_schedule:
  sources:
    - name: joondalup_wa_gov_au
      args:
        number: "2"
        street: "Ashburton Drive"
        suburb: "Heathridge"
```

```yaml
waste_collection_schedule:
  sources:
    - name: joondalup_wa_gov_au
      args:
        mapkey: "785"
```

## How to find your mapkey, if you want to use it
Search for your collection schedule on the Joondalup website. Wait for the schedule to load and the property image to be displayed. Right-click on the property image and _copy image address_. Examine the copied url, your mapkey is shown at the end of the url.



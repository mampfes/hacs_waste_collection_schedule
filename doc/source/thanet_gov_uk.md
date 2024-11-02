# Thanet District Council

Support for schedules provided by [Thanet District Council](https://www.thanet.gov.uk/online-services/your-collection-day/), serving the
district of Thanet, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: thanet_gov_uk
      args:
        postcode: Postcode
        street_address: Street Address
        uprn: Unique Property Reference Number (UPRN)
```

### Configuration Variables

**postcode**  
*(string) (optional)*

**street_address**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

Supply both postcode and street_address args, or just the uprn argument

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: thanet_gov_uk
      args:
        uprn: "100061108233"
```

### Using street address and postcode

```yaml
waste_collection_schedule:
    sources:
    - name: thanet_gov_uk
      args:
        postcode: "CT7 0DN"
        street_address: "12 Woodland Avenue"
```

## How to find the values for arguments above

You can find your UPRN by going to the [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and searching there.
If you're entering a postcode and street address you will need to use your post code with a space and for street address use the text before the first comma in the options provided yo you on Thanet's bin schedule webpage - e.g. if their site says "Lovely Cottage, Thanet,..." then use "Lovely Cottage" as the street address, if it says "1 London Road, Thanet..." then you need to enter "1 London Road".

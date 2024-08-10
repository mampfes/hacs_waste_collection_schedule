# Antrim and Newtownabbey

Support for schedules provided by [Antrim and Newtownabbey](https://antrimandnewtownabbey.gov.uk), serving Antrim and Newtownabbey, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: antrimandnewtownabbey_gov_uk
      args:
        id: ID
        uprn: UPRN
```

### Configuration Variables

**id**  
*(Integer) (optional)* required for regular bin collection

**uprn**
*(Integer) (optional)* required for recycling bin collection

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: antrimandnewtownabbey_gov_uk
      args:
        id: 1456 # Required fore regular bin collection
        uprn: 185354344 # Required for recycling bin collection
        
```

## How to get the source argument

### ID for regular bin collection

Goto [https://antrimandnewtownabbey.gov.uk/residents/bins-recycling/bins-schedule/](https://antrimandnewtownabbey.gov.uk/residents/bins-recycling/bins-schedule/) and search for your address. Click on `View full bin schedule` you will now see the `id` in the URL. It's the number after `id=`.

e.g. for <https://antrimandnewtownabbey.gov.uk/residents/bins-recycling/bins-schedule/?Id=1456> the id is `1456`.

### UPRN for recycling bin collection

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

alternatively, you can find your uprn in the URL when searching your address here: <https://www.brysonrecycling.org/northern-ireland/kerbside-collections/collection-day>

e.g. if the URL is `https://www.brysonrecycling.org/northern-ireland/kerbside-collections/collection-day?district=newtownabbey&uprn=NI185354344&submit=` then the uprn is `185354344`.

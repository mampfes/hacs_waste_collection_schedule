# London Borough of Lewisham

Support for schedules provided by the [London Borough of Lewisham](https://lewisham.gov.uk/myservices/wasterecycle/your-bins/collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: lewisham_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        post_code: POST_CODE
        name: HOUSE_NAME
        number: HOUSE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (optional)*

This is required if you do not supply any other options. (Using this removes the need to do an address look up web request)

**name**  
*(string) (optional)*

This is required if you supply a Postcode and do not have a house number.

**number**  
*(string) (optional)*

This is required if you supply a Postcode and have a house number.

**post_code**  
*(string) (optional)*

This is required if you do not supply a UPRN. Single space between 1st and 2nd part of postcode is optional.

#### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [https://www.findmyaddress.co.uk/](https://www.findmyaddress.co.uk/) and entering in your address details.
Otherwise you can inspect the web requests the Peterborough Council website makes when entering in your postcode and then selecting your address.

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: lewisham_gov_uk
      args:
        uprn: 100021937156
```

## Example using Address lookup

```yaml
waste_collection_schedule:
    sources:
    - name: lewisham_gov_uk
      args:
        post_code: SE231LB
        number: 23
```

# Ashfield District Council

Support for schedules provided by [Ashfield District Council](https://www.ashfield.gov.uk/), serving Ashfield district in Nottinghshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ashfield_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        post_code: POST_CODE
        name: HOUSE_NAME
        number: HOUSE_NUMBER
```

### Configuration Variables

### Configuration Variables

**uprn**<br>
*(string) (optional)*

This is required if you do not supply any other options. (Using this removes the need to do an address look up web request)

**name**<br>
*(string) (optional)*

This is required if you supply a Postcode and do not have a house number.

**number**<br>
*(string) (optional)*

This is required if you supply a Postcode and have a house number.

**post_code**<br>
*(string) (optional)*

This is required if you do not supply a UPRN. Single space between 1st and 2nd part of postcode is optional.

#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
Otherwise you can inspect the web requests the Ashfield District Council website makes when entering in your postcode and then selecting your address.

## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: ashfield_gov_uk
      args:
        uprn: 100032105121
```

## Example using Address lookup
```yaml
waste_collection_schedule:
    sources:
    - name: ashfield_gov_uk
      args:
        post_code: "NG17 8DA"
        name: "Ashfield District Council"
```
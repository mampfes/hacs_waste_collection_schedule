# Telford and Wrekin Council

Support for schedules provided by [Telford and Wrekin Council](https://www.telford.gov.uk/), serving Telford and Wrekin in Shropshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: telford_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        post_code: POST_CODE
        name_number: HOUSE_NAME_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (optional)*

This is required if you do not supply any other address options. (Using this removes the need to do an address look up web request)

**name_number**<br>
*(string) (optional)*

This is required if you supply a Postcode and should contain the house name or number.

**post_code**<br>
*(string) (optional)*

This is required if you do not supply a UPRN. Single space between 1st and 2nd part of postcode is optional.

#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.


## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: telford_gov_uk
      args:
        uprn: 100032105121
```

## Example using Address lookup
```yaml
waste_collection_schedule:
    sources:
    - name: telford_gov_uk
      args:
        post_code: "TF4 2SF"
        name_number: "10"
```
## Example using Address lookup
```yaml
waste_collection_schedule:
    sources:
    - name: telford_gov_uk
      args:
        post_code: "TF2 3NR"
        name_number: "Abbey House"
```
## Returned collectons
The API will return the next collection date for each container type. This will typically be the collections for the next 2 weeks but may vary over holiday periods

## Returned collection types

### General (Red)
Red top container for general waste

### Recycling (Purple/Blue)
Purple top container for glass / cans and Blue bag for paper / cardboard 

### Garden (Green)
Green container for garden waste

### Food (Silver)
Silver coltainer for food waste

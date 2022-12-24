# Environment First

Consolidated support for schedules provided by [Eastbourne Borough Council](https://www.lewes-eastbourne.gov.uk/bins-waste-and-recycling/) and [Lewes District Council](https://www.lewes-eastbourne.gov.uk/bins-waste-and-recycling/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: environmentfirst_co_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        post_code: POST_CODE
        name: HOUSE_NAME
        number: HOUSE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (optional) (preferred method)*

This is required if you do not supply any other options. Using a UPRN removes the need to do an address look up using web requests.

**post_code**  
*(string) (optional)*

This is required if you do not supply a UPRN. Single space between 1st and 2nd part of postcode is optional.

**number**  
*(string) (optional)*

This is required if you supply a Postcode and have a house number.

**name**  
*(string) (optional)*

This is required if you supply a Postcode and you have a house name rather than a house number.

## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: environmentfirst_co_uk
      args:
        uprn: 100060091178
```

## Example using Address lookup (Postcode and house number)
```yaml
waste_collection_schedule:
    sources:
    - name: environmentfirst_co_uk
      args:
        post_code: BN228SG
        number: 3
```

## Example using Address lookup (Postcode and house name)
```yaml
waste_collection_schedule:
    sources:
    - name: environmentfirst_co_uk
      args:
        post_code: BN7 3LG
        name: Garden Cottage
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

Otherwise you can inspect the web requests on the [Environment First](https://www.environmentfirst.co.uk/) having searched using your address details. Your UPRN is the collection of digits at the end of the URL, for example: *https://www.environmentfirst.co.uk/house.php?uprn=`100060091178`*

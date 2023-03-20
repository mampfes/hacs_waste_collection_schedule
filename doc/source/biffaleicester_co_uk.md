# Biffa Leicester

Support for schedules provided by [Biffa Leicester](https://biffaleicester.co.uk/services/waste-collection-days), serving Leicester (UK).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: biffaleicester_co_uk
      args:
        uprn: UPRN
        post_code: POST_CODE
        number: NUMBER
```

### Configuration Variables

**uprn**  
*(string) (optional)*

This is required if you do not supply any other options. (Using this removes the need to do an address look up web request)

**number**  
*(string) (optional)*

This is required if you supply a Postcode.

**post_code**  
*(string) (optional)*

This is required if you do not supply a UPRN. Single space between 1st and 2nd part of postcode is optional.

#### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can inspect the web requests the Peterborough Council website makes when entering in your postcode and then selecting your address.

## Example using Address lookup

```yaml
waste_collection_schedule:
    sources:
    - name: biffaleicester_co_uk
      args:
        post_code: "LE5 5QD"
        number: "30"
```

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: biffaleicester_co_uk
      args:
        uprn: "002465020938"
```

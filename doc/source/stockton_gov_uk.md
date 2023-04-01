# Stockton-on-Tees Borough Council

Support for schedules provided by [Stockton-on-Tees Borough Council](https://www.stockton.gov.uk/), serving Stockton-on-Tees Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stockton_gov_uk
      args:
        uprn: UPRN
        
```

### Configuration Variables

**uprn**  
*(Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stockton_gov_uk
      args:
        uprn: 10003082467
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providing your address details.

Alternatively you can use the browser inspection tools. In network traffic the last response after entering the postcode and pressing `Find address` returns JSON containing the UPRN for all addresses in this postcode range.

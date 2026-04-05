# City of Cincinnati, OH

Support for schedules provided by [City of Cincinnati](https://www.cincinnati.gov/), serving Cincinnati, OH, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cincinnati_gov
      args:
        addressid: ADDRESS_ID
```

### Configuration Variables

**addressid**  
*(String) (required)* Your address ID from Cincinnati's system (e.g. "00010GRAND0703640000")

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cincinnati_gov
      args:
        addressid: "00010GRAND0703640000"
```

## How to get the source arguments

1. Go to [Cincinnati Services](https://cagismaps.hamilton-co.org/caborc/cinciservices/)
2. Search for your address
3. The address ID can be found in the URL after selecting your address

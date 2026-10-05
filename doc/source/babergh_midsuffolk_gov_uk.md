# Babergh and Mid Suffolk District Councils

Support for schedules provided by [Babergh and Mid Suffolk District Councils](https://www.midsuffolk.gov.uk).

Source for Babergh and Mid Suffolk District Council bin collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: babergh_midsuffolk_gov_uk
      args:
        uprn: UPRN
        council: COUNCIL
```

### Configuration Variables

**uprn**  
*(string) (required)*

**council**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: babergh_midsuffolk_gov_uk
      args:
        uprn: '100091488908'
        council: midsuffolk
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) by entering your address details, and choose your council: `midsuffolk` (Mid Suffolk District Council) or `babergh` (Babergh District Council).

This source only serves the areas covered by the existing Babergh and Mid Suffolk District Councils. It does not cover the new councils planned for Suffolk under the local government reorganisation, which are not expected to be live until at least April 2028.

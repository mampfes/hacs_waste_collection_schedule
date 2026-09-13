# Bromsgrove & Redditch Councils

Support for the shared bin collection lookup used by:
    - [Bromsgrove District Council](https://www.bromsgrove.gov.uk/)
    - [Redditch Borough Council](https://www.redditchbc.gov.uk/)

Bromsgrove and Redditch run a shared waste service and both publish the same
"BinCollections" web app, each on their own council domain.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bromsgrove_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        postcode: POSTCODE
        council: COUNCIL_NAME
```

### Configuration Variables

**uprn**  
*(string)*

The "Unique Property Reference Number" for your address. You can find it by searching for your address at <https://www.findmyaddress.co.uk/>.

**postcode**  
*(string)*

The Post Code for your address. This needs to match the postcode corresponding to your UPRN.

**council**  
*(string) (optional)*

Defaults to `bromsgrove`, should be one of:
    - `bromsgrove`
    - `redditch`

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: bromsgrove_gov_uk
      args:
        uprn: 10094552413
        postcode: B61 8DA
```

## Example for Redditch Borough Council

```yaml
waste_collection_schedule:
    sources:
    - name: bromsgrove_gov_uk
      args:
        uprn: 10094552413
        postcode: B97 5TB
        council: redditch
```

## Returned Collections

This source will return the next collection date for each container type.

## Returned collection types

### Household Collection

Grey bin is for general waste.

### Recycling Collection

Green bin is for dry recycling (metals, glass, plastics, paper and card).

### Garden waste Chargeable Collections

Brown bin is for garden waste. This is an annual chargeable service.

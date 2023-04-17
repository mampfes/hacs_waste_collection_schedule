# Basildon Council

Support for schedules provided by [Basildon Council](https://www3.basildon.gov.uk/website2/postcodes.nsf/frmMyBasildon), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
      args:
        postcode: POSTCODE
        address: FIRST LINE OF ADDRESS (X, STREET NAME)
```

### Configuration Variables

**postcode**  
*(string) (required)*
**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
      args:
        postcode: CM111BJ
        address: 6, HEADLEY ROAD
```

## How to get the source argument

An easy way to discover your Postcode and address used by this service is by going to <https://www3.basildon.gov.uk/website2/postcodes.nsf/frmMyBasildon> and entering in your address details.

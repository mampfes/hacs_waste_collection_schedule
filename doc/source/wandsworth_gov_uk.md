# Wandsworth Council

Support for schedules provided by [Wandsworth
Council](https://www.wandsworth.gov.uk/my-property/), serving the
London Borough of Wandsworth.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wandsworth_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: wandsworth_gov_uk
      args:
        uprn: "100022645573"
```

## How to get the source argument

The UPRN code can be found in the url after entering your
postcode and selecting your address on the [Wandsworth My Property
page](https://www.wandsworth.gov.uk/my-property/). You should look
for a UPRN code in the URL it will look like this:
https://www.wandsworth.gov.uk/my-property/?UPRN=100022645573&propertyidentified=Select#result

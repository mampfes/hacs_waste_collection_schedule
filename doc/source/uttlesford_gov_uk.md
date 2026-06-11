# Uttlesford District Council

Support for schedules provided by [Uttlesford District Council](http://bins.uttlesford.gov.uk/), serving Uttlesford, Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new West Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: uttlesford_gov_uk
      args:
        house: HOUSE_REFERENCE_NUMBER
```

### Configuration Variables

**house**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: uttlesford
      args:
        house: "12345-Monday"

```

## How to find your `house`

You can find your house reference number by going to https://bins.uttlesford.gov.uk and searching for your property.
The house reference for your property will be displayed in the url in your browser once you have successfully selected your property.
e.g. http://bins.uttlesford.gov.uk/collections.php?postcode=cm6+1aa&**house=12345-Tuesday**&x=156&y=29

## Returned collections

The API will return the next collection date for each container type. This will typically be the collections for the next 2 weeks but may vary over holiday periods

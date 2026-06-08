# Norwich City Council

Support for the next collection day provided by [Norwich City Council](https://www.norwich.gov.uk/bins-and-recycling), serving Norwich, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Norfolk, please continue to use the source for your current area as long as it's still working. New sources for the new West Norfolk, Greater Norwich, and East Norfolk councils are not expected to be live until at least April 2028, when the councils themselves officially come into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: norwich_gov_uk
      args:
        property_name_or_number: PROPERTY_NAME_OR_NUMBER
        street_name: STREET_NAME
        postcode: POSTCODE
```

### Configuration Variables

**property_name_or_number**  
*(string) (required)*

**street_name**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: norwich_gov_uk
      args:
        property_name_or_number": "33"
        street_name": "Carrow Road"
        postcode": "NR1 1HS"
```

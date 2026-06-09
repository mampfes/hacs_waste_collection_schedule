# Thurrock

Support for schedules provided by [Thurrock](https://www.thurrock.gov.uk/), serving Thurrock, Essex, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Essex, please continue to use the source for your current area as long as it's still working. New sources for the new South West Essex Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: thurrock_gov_uk
      args:
        street: STREET
        town: TOWN
        
```

### Configuration Variables

**street**  
*(String) (required)*

**town**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: thurrock_gov_uk
      args:
        street: Camden Close
        town: Chadwell St Mary
        
```

## How to get the source argument

Find the parameter of your address using [https://www.thurrock.gov.uk/household-bin-collection-days/normal-collections-and-public-holidays](https://www.thurrock.gov.uk/household-bin-collection-days/normal-collections-and-public-holidays) and write them exactly like on the web page.

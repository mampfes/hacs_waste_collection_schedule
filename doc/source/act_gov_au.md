# Australian Captial Territory (ACT)

Support for schedules provided by [ACT Goverment City Services]([https://www.canadabay.nsw.gov.au/](https://www.cityservices.act.gov.au/)).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: SUBURB
```

### Configuration Variables

**suburb**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: act_gov_au
      args:
        suburb: BRUCE
```

## How to get the source arguments

Visit the [ACT City Service's Bin Collection Calendar](https://www.cityservices.act.gov.au/recycling-and-waste/collection/bin-collection-calendar) page and look for your suburb.  The arguments should be in all uppercase of what is found in the dropdown.

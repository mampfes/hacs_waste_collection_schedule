# Castle Point Borough Council

Support for schedules provided by [Castle Point Borough Council](https://www.castlepoint.gov.uk).

Source for Castle Point Borough Council waste collections.

## Configuration via configuration.yaml

### Using roadID

```yaml
waste_collection_schedule:
  sources:
    - name: castlepoint_gov_uk
      args:
        roadID: ROADID
```

### Using street_name

```yaml
waste_collection_schedule:
  sources:
    - name: castlepoint_gov_uk
      args:
        street_name: STREET_NAME
```

### Configuration Variables

**roadID**  
*(string) (alternative)*

**street_name**  
*(string) (alternative)*

Provide one of: `roadID` or `street_name`.

## Example

### Using roadID

```yaml
waste_collection_schedule:
  sources:
    - name: castlepoint_gov_uk
      args:
        roadID: '4448'
```

### Using street_name

```yaml
waste_collection_schedule:
  sources:
    - name: castlepoint_gov_uk
      args:
        street_name: Ash Road
```

## How to get the source arguments

Go to https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet&f=homepage1 and either enter your street name in the search box or select the first letter of your street. Click on the street name and look for the roadID in the URL, or enter the street name (only needed if you don't provide roadID). If two towns in the borough share a street name, add the town in brackets, e.g. 'HIGH STREET (CANVEY ISLAND)'.

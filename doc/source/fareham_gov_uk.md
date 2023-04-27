# Fareham Council

The fareham gov uk website does not return all future collection dates, only the next upcoming one. You can test different addresses at <https://www.fareham.gov.uk/internetlookups/search.aspx?list=DomesticBinCollections>.

Credit to Fareham Borough Council for all data fetched from their API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fareham_gov_uk
      args:
        road_name: Road name
        postcode: Post code
```

### Configuration Variables

**road_name**  
_(string) (required)_  
The name of the road the house is on

**postcode**  
_(string) (required)_  
The post code for the house

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fareham_gov_uk
      args:
        road_name: Hunts pond road
        postcode: PO14 4PL
```

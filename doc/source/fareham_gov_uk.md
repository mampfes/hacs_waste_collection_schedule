# Fareham Council

Support for schedules provided by Fareham Council, serving Fareham, Hampshire, UK.

The fareham gov uk website does not return all future collection dates, only the next upcoming one. You can test different addresses at <https://www.fareham.gov.uk/internetlookups/search.aspx?list=DomesticBinCollections2025on>.

Credit to Fareham Borough Council for all data fetched from their API.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new South East Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

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
The name of the road the house is on. You can include an optional house number (for example `22 street`).

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

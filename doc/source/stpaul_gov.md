# City of Saint Paul, MN

Support for schedules provided by [City of Saint Paul, MN](https://www.stpaul.gov/departments/public-works/garbage-and-recycling).

Source for residential garbage and recycling in Saint Paul, MN, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stpaul_gov
      args:
        address: ADDRESS
        every_other_week_garbage: EVERY_OTHER_WEEK_GARBAGE
```

### Configuration Variables

**address**  
*(string) (required)*

**every_other_week_garbage**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stpaul_gov
      args:
        address: 1006 Summit Ave
```

## How to get the source arguments

Enter your street address with the house number, e.g. '1006 Summit Ave' (city, state and ZIP are optional). It is looked up on the city's Garbage & Recycling Day Map (https://stpaul.maps.arcgis.com/apps/instant/lookup/index.html?appid=5b3d5ace287e428596cf18fd025fa6fb). Turn on 'Every-other-week garbage collection' if you chose that service; garbage is then collected in the weeks shaded on the city's collection calendar. Downtown recycling has no fixed day and is not included.

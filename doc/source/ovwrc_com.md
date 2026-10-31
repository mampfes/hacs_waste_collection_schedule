# Ottawa Valley Waste Recovery Centre (Petawawa)

Support for schedules provided by [Ottawa Valley Waste Recovery Centre (Petawawa)](https://ovwrc.com).

Source for the Town of Petawawa's curbside collection calendar.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ovwrc_com
      args:
        day: DAY
```

### Configuration Variables

**day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ovwrc_com
      args:
        day: Wednesday
```

## How to get the source arguments

Open https://ovwrc.com/curbside-collection-calendars/ and consult the map in the Town of Petawawa calendar to find your regular Wednesday, Thursday or Friday route. Choose that usual day, even in a holiday week; the source uses the actual printed collection dates. It reads green carts, blue paper boxes, yellow container bins, garbage and natural Christmas trees. Separate leaf/yard-waste and large-item collections are not supported. Pembroke and Laurentian Valley use other calendars and are not supported. First-time PDF parsing can take several seconds; an unchanged document reuses the parsed grid.

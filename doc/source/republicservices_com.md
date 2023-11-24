# Republic Services

Support for schedules provided by [Republic Services](https://republicservices.com), serving the municipality all over the United States of America.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: STREET_ADDRESS
        method: METHOD
```

### Configuration Variables

**street_address**  
*(string) (required)*

**method**  
*(int) (optional)*

_method: 1_

Waste type categories are returned as per the Republic Services entries. This is the default behaviour if no arg is provided. 

method: 2

Recycling waste type categories described as Yard Waste are returned as a "Yard Waste" waste type rather than source "Recycling" waste type.

## Example (method: 1)

```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: "8957 Park Meadows Dr, Elk Grove, CA 95624"
        method: 1
```
```bash
2023-10-24 : Recycle [mdi:leaf]
2023-10-31 : Recycle [mdi:recycle]
2023-11-14 : Recycle [mdi:recycle]
2023-11-28 : Recycle [mdi:recycle]
2023-12-12 : Recycle [mdi:recycle]
2023-12-26 : Recycle [mdi:recycle]
2023-10-24 : Solid Waste [mdi:trash-can]
```

## Example (method: 2)
```yaml
waste_collection_schedule:
  sources:
    - name: republicservices_com
      args:
        street_address: "8957 Park Meadows Dr, Elk Grove, CA 95624"
        method: 2
```
```bash
2023-10-24 : Yard Waste [mdi:leaf]
2023-10-31 : Recycle [mdi:recycle]
2023-11-14 : Recycle [mdi:recycle]
2023-11-28 : Recycle [mdi:recycle]
2023-12-12 : Recycle [mdi:recycle]
2023-12-26 : Recycle [mdi:recycle]
2023-10-24 : Solid Waste [mdi:trash-can]
```
## How to check the street address

The street address can be tested [here](https://republicservices.com).

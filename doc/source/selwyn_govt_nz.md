# Selwyn District Council

Support for schedules provided by [Selwyn District Council](https://www.selwyn.govt.nz/), serving the Selwyn District, New Zealand.

The source queries the council's public ArcGIS property service and returns the next eight weeks of collections for the property: weekly rubbish, fortnightly recycling, and (where the property has an organics service) weekly organics.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: selwyn_govt_nz
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*  
Your street address within the Selwyn District, including the town, exactly as it appears in the council's address search (e.g. `30 Tennyson Street Rolleston`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: selwyn_govt_nz
      args:
        address: 30 Tennyson Street Rolleston
```

## How to get the source argument

Visit the council's [collection days and routes](https://www.selwyn.govt.nz/services/rubbish-and-recycling/collection-days-and-routes) page and search for your property. Copy the address as shown in the search result and use it as the `address` argument. A partial address is matched as a prefix; include the town to avoid matching multiple properties.

## Notes / Limitations

- Rubbish is collected weekly and recycling fortnightly (on the weeks matching the property's recycling schedule). Organics is collected weekly **where the property has an organics service** — some areas (e.g. a number of rural properties) have no kerbside organics, in which case no organics collections are returned. All of a property's bins share the same weekday.
- The council's data does not encode public-holiday adjustments, so collections that are shifted around New Zealand public holidays are not reflected. This limitation is shared with other New Zealand sources.

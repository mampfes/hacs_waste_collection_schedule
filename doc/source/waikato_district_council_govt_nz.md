# Waikato District Council

Support for schedules provided by [Waikato District Council](https://www.waikatodistrict.govt.nz/), serving the Waikato District, New Zealand.

The source queries the council's public rubbish and recycling collection address search and returns the next 26 weeks of collections for the property.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: waikato_district_council_govt_nz
          args:
            address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*  
Your street address within the Waikato District, including the town, e.g. `18 Example Drive, Huntly`.

## Example

```yaml
waste_collection_schedule:
    sources:
        - name: waikato_district_council_govt_nz
          args:
            address: 18 Example Drive, Huntly
```

## How to get the source argument

Visit the council's [rubbish and recycling collection](https://www.waikatodistrict.govt.nz/services-facilities/rubbish-and-recycling/rubbish-and-recycling-services/rubbish-and-recycling-collection) page and search for your property using the address search box. Use the same address as the `address` argument, including the town/suburb if the street name is ambiguous. If the address cannot be matched uniquely, the integration's error message will list the closest known addresses.

## Notes / Limitations

- Rubbish, glass/mixed recycling, paper and card (and, in some areas, food scraps) are collected together on the same weekly kerbside day, so a single combined "Rubbish and Recycling" entry is returned per collection day.
- Properties served by a monthly resource-recovery drop-off point, a self-service transfer station, or with no kerbside service, are not supported — the council's own page does not provide a fixed weekly day for these either.
- The council's data does not encode public-holiday adjustments beyond the very next collection date, so collections further in the future that are shifted around New Zealand public holidays may not be reflected exactly. This limitation is shared with other New Zealand sources.

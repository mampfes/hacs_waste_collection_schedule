# Lisburn and Castlereagh City Council

Support for schedules provided by [Lisburn and Castlereagh City Council](https://www.lisburncastlereagh.gov.uk/resident/bins-and-recycling/household-waste/collection-days-and-holiday-information), serving the city of Lisburn and Castlereagh

## Configuration via configuration.yaml

(recommended)

```yaml
waste_collection_schedule:
    sources:
    - name: lisburn_castlereagh_gov_uk
      args:
        property_id: "PROPERTY_ID"
```

or (not recommended)

```yaml
waste_collection_schedule:
    sources:
        - name: lisburn_castlereagh_gov_uk
          args:
            post_code: "BT28 1AG"
            house_number: "19A"
```

### Configuration Variables

**property_id**  
*(string) (required if post_code not provided)*

**post_code**  
*(string) (required if premises_id not provided)*

**house_number**  
*(string) (required if premises_id not provided)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: lisburn_castlereagh_gov_uk
      args:
        property_id: "DYYSm8Ls8XxGi3Nq"
```

## How to get the property_id argument

The property_id can be found in the URL when looking up your
bin collection days at [Lisburn and Castlereagh bin collection days](https://lisburn.isl-fusion.com).

## Why property_id over post_code and house_number?

The code has to do a search by post code and house number then look up the bin collection time using property ID

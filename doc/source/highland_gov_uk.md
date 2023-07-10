# Highland

Support for schedules provided by [Highland](https://www.highland.gov.uk/), serving Highland, Scotland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: highland_gov_uk
      args:
        record_id: RECORD ID
        
```

### Configuration Variables

**record_id**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: highland_gov_uk
      args:
        record_id: 2004443
        
```

## How to get the source argument

Go to <https://www.highland.gov.uk/bindays> and search for your corresponding entry. The URL should look something like this: `https://www.highland.gov.uk/directory_record/2004443/allangrange_mains_road_black_isle` the number after directory_record is your record_id (here 2004443).

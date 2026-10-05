# Scottish Borders Council

Support for schedules provided by [Scottish Borders Council](https://scotborders-live-portal.bartecmunicipal.com/Embeddable/CollectionCalendar).

Source for Scottish Borders Council (Bartec Municipal)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: scotborders_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: scotborders_gov_uk
      args:
        uprn: '116073632'
        postcode: TD9 9HL
```

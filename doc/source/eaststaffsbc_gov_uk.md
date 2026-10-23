# East Staffordshire Borough Council

Support for schedules provided by [East Staffordshire Borough Council](https://www.eaststaffsbc.gov.uk/).

Source for East Staffordshire Borough Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eaststaffsbc_gov_uk
      args:
        uid: UID
```

### Configuration Variables

**uid**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eaststaffsbc_gov_uk
      args:
        uid: 103368
```

## How to get the source arguments

Search for your address on the [East Staffordshire collection dates page](https://www.eaststaffsbc.gov.uk/bins-rubbish-recycling/collection-dates). The number at the end of the resulting address (`.../collection-dates/<uid>`) is your `uid`.

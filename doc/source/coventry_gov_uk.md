# Coventry City Council

Support for schedules provided by [Coventry City Council](https://www.coventry.gov.uk/rubbishandrecycling), serving Coventry, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: coventry_gov_uk
      args:
        street: STREET
```

### Configuration Variables
**street**  
*(string) (required)*<br>
Your street name as it appears on the Coventry City Council website.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: coventry_gov_uk
      args:
        street: "Linwood Drive"
```

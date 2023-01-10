# Maroondah City Council

Support for schedules provided by [Maroondah City Council](https://www.maroondah.vic.gov.au).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maroondah_vic_gov_au
      args:
        address: ADDRESS # see 'How to get the source argument below'
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maroondah_vic_gov_au
      args:
        address: 14 Main Street, CROYDON 3136
```

## How to get the source argument

Simply enter your street number and name as if you're searching on the online tool. Note that the first result will be selected if there are multiple search results.

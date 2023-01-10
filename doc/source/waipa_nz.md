# Waipa District Council

Support for schedules provided by [Waipa District Council](https://aucklandcouncil.govt.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: waipa_nz
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
    - name: waipa_nz
      args:
        address: 1 Acacia Avenue
```

## How to get the source argument

Simply enter your street number and name as if you're searching on the online tool. Note that the first result will be selected if there are multiple search results.

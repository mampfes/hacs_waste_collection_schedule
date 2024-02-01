# Tauranga City Council

Support for schedules provided by [Tauranga City Council](https://www.tauranga.govt.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tauranga_govt_nz
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
    - name: tauranga_govt_nz
      args:
        address: "1 Santa Monica Drive"
```

## How to get the source argument

Simply enter your street number and name as if you're searching on the online tool. Note that the first result will be selected if there are multiple search results.

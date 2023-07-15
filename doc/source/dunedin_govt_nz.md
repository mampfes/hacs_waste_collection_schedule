# Horowhenua District Council

Support for schedules provided by [Dunedin District Council Kerbside Rubbish & Recycling Services](https://www.dunedin.govt.nz/do-it-online/search/collection-days).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dunedin_govt_nz
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dunedin_govt_nz
      args:
        address: "118 High Street Dunedin"
```

## How to get the source argument
Visit the [Dunedin District Council Kerbside Collection Days](https://www.dunedin.govt.nz/do-it-online/search/collection-days) page and search for your address. The `address` argument should match how the website displays address alongside your next collection details.

Note: For addresses with hyphenated numbers, the whitespace is important. For example, the website tends to use the format "2 - 6 Random Road Dunedin", so resist changing it to "2-6 Random Road Dunedin".

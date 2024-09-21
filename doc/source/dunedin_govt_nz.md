# Dunedin District Council

Support for schedules provided by [Dunedin District Council Kerbside Rubbish & Recycling Services](https://www.dunedin.govt.nz/do-it-online/search/collection-days). It uses the endpoint of the [DCC Kerbside Collection APP](https://play.google.com/store/apps/details?id=com.dcc.recyclingassistant).

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

Use the [DCC Kerbside Collection APP](https://play.google.com/store/apps/details?id=com.dcc.recyclingassistant) ([IOS](https://apps.apple.com/us/app/dcc-kerbside-collections/id1490010132?ls=1)) and search for your address. The `address` argument should match how the APP displays the address alongside your next collection details.

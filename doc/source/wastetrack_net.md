# WasteTrack (3Logix)

Support for schedules provided by [WasteTrack (3Logix)](https://v2.wastetrack.net).

Source for councils using the WasteTrack self-service locator by 3Logix.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wastetrack_net
      args:
        address: ADDRESS
        key: KEY
```

### Configuration Variables

**address**  
*(string) (required)*

**key**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wastetrack_net
      args:
        address: 16 MacMahon Street, Hurstville
        key: da1d834c-3d97-4f96-9d60-4107ef0a53e6
```

## How to get the source arguments

Enter your street address as the council's bin day lookup shows it, e.g. '16 MacMahon Street, Hurstville'. The key is pre-filled when you pick your council.

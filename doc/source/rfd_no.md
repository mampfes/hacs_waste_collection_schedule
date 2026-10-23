# Renovasjonsselskapet for Drammensregionen IKS (RfD)

Support for schedules provided by [Renovasjonsselskapet for Drammensregionen IKS (RfD)](https://www.rfd.no).

Source for RfD waste collection schedules

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rfd_no
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
    - name: rfd_no
      args:
        address: Bragernes Torg 13, Drammen
```

## How to get the source arguments

Search for your address at rfd.no/avfallshenting. Use the address exactly as shown in the result list, for example 'Bragernes Torg 13, Drammen'.

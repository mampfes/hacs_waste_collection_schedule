# Renovasjonsselskapet for Drammensregionen IKS (RfD)

Support for schedules provided by [Renovasjonsselskapet for Drammensregionen IKS (RfD)](https://www.rfd.no), serving the Drammen region, Norway.

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
*(String) (required)*

The address as shown in the RfD address search results, for example `Grønland 1, Drammen`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rfd_no
      args:
        address: Grønland 1, Drammen
```

## How to get the source argument

Visit [https://www.rfd.no/avfallshenting](https://www.rfd.no/avfallshenting), search for your address, and use the address exactly as shown in the result list.

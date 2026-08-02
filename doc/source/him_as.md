# Haugaland Interkommunale Miljøverk (HIM)

Support for schedules provided by [Haugaland Interkommunale Miljøverk (HIM)](https://him.as), serving Haugesund and surrounding municipalities, Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: him_as
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

The address exactly as shown in the HIM `tømmekalender` address search results, for example `Leiv Eirikssons Gate 10`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: him_as
      args:
        address: Leiv Eirikssons Gate 10
```

## How to get the source argument

Visit [https://him.as/tommekalender/](https://him.as/tommekalender/), search for your address and use the address exactly as shown in the result, e.g. `Leiv Eirikssons Gate 10`.

If your search term matches more than one address, the source will raise an error listing the possible addresses to choose from — use the exact one from that list.

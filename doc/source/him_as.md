# Haugaland Interkommunale Miljøverk (HIM)

Support for schedules provided by [Haugaland Interkommunale Miljøverk (HIM)](https://him.as).

Source for Haugaland Interkommunale Miljøverk (HIM) waste collection schedules, covering Haugesund and surrounding municipalities, Norway.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: him_as
      args:
        address: Leiv Eirikssons Gate 10
```

## How to get the source arguments

Visit https://him.as/tommekalender/, search for your address and use the address exactly as shown, e.g. 'Leiv Eirikssons Gate 10'.

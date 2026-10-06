# Avfall Sør, Kristiansand

Support for schedules provided by [Avfall Sør, Kristiansand](https://avfallsor.no/).

Source for Avfall Sør, Kristiansand.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: avfallsor_no
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
    - name: avfallsor_no
      args:
        address: Auglandslia 1, Kristiansand
```

## How to get the source arguments

Enter your address as shown on [avfallsor.no](https://avfallsor.no/) (Finn hentedag), e.g. 'Auglandslia 1, Kristiansand'. The city may be left out.

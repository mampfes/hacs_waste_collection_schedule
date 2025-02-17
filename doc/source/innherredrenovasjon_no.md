# Innherred Renovasjon, Norway

Support for schedules provided by [Innherred Renovasjon](https://innherredrenovasjon.no/), serving Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: innherredrenovasjon_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: innherredrenovasjon_no
      args:
        address: "Gevingåsen 122"
        
```

## How to get the source argument

Visit [https://innherredrenovasjon.no/](https://innherredrenovasjon.no/) and enter your address. On the results page, use your address as shown in the main heading.
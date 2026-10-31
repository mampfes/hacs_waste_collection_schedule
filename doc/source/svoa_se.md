# Stockholm vatten och avfall

Support for schedules provided by [SVOA](https://www.stockholmvattenochavfall.se/villa-och-radhus/avfallstjanster/nar-kommer-sopbilen/).

Source for Stockholm municipality in Sweden

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: svoa_se
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
    - name: svoa_se
      args:
        address: "Lussekattsvägen 10, Sköndal, 128 69"
```

## How to get the source arguments

Enter the address as the SVOA website writes it, street and number followed by the locality and postal code.

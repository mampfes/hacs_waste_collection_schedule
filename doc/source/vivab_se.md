# VA Syd Sophämntning

Support for schedules provided by [VIVAB](https://vivab.se/%C3%A5tervinning-avfall/hushallsavfall/vara-abonnemang/h%C3%A4mtning-av-hush%C3%A5llsavfall), serving the municipality of Varberg and Falkenberg, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: Västra Vallgatan 2, Varberg
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://vivab.se/%C3%A5tervinning-avfall/hushallsavfall/vara-abonnemang/h%C3%A4mtning-av-hush%C3%A5llsavfall).

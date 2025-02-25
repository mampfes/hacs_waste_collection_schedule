# VA Syd Sophämntning

Support for schedules provided by [VIVAB](https://vivab.se/%C3%A5tervinning-avfall/hushallsavfall/vara-abonnemang/h%C3%A4mtning-av-hush%C3%A5llsavfall), serving the municipality of Varberg and Falkenberg, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: STREET_ADDRESS
        building_id: BUILDING_ID
```

### Configuration Variables

**street_address**  
*(string) (required)* The address of the property to get the waste collection schedule for. Should end with Varberg or Falkenberg.

**building_id**  
*(string) (optional)* You can also provide the building id, which is shown behind the search result on the website. You still need to set street address to "Varberg" or "Falkenberg". Might be required if there are two results for the same address.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: Västra Vallgatan 2, Varberg
```

```yaml
waste_collection_schedule:
  sources:
    - name: vivab_se
      args:
        street_address: Falkenberg
        building_id: "9593062021"
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://vivab.se/%C3%A5tervinning-avfall/hushallsavfall/vara-abonnemang/h%C3%A4mtning-av-hush%C3%A5llsavfall).

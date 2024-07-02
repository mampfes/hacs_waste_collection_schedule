# NVAA (Norrtälje Vatten och Avfall)

Support for schedules provided by [NVAA](https://www.nvaa.se), Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nvaa_se
      args:
        street_address: STREET ADDRESS
        
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: nvaa_se
      args:
        streetAddress: "Gustav Adolfs väg 24"
```

## How to get the buildingId argument

1. Go to [https://www.nvaa.se/sjalvservice](NVAA's self-serivce portal).
2. Open web inspector and have filter by XHR/Fetch requests
3. Type in your address including house number and click on it.
4. Use the address as it appears in the search.
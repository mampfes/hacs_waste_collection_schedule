# Ljusdal Energi

Support for schedules provided by [Ljusdal Energi](https://ljusdalenergi.se).

Source for Ljusdal Energi waste collection, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ljusdalenergi_se
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
    - name: ljusdalenergi_se
      args:
        address: "Norra J\xE4rnv\xE4gsgatan 21, Ljusdal"
```

## How to get the source arguments

Enter your street address and town as shown in the address search on the [Hämtningsdagar page](https://ljusdalenergi.se/renhallning/privatpersoner/sophamtning/nar-hamtas-dina-sopor/hamtningsdagar.html), e.g. `Norra Järnvägsgatan 21, Ljusdal`. The town is optional unless the same address exists in several towns. Ljusdal Energi's backend only answers requests from Swedish internet connections.

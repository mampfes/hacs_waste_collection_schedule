# RenoWeb

Support for schedules provided by [RenoWeb](https://renoweb.dk).

RenoWeb collections

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: renoweb_dk
      args:
        municipality: MUNICIPALITY
        address: ADDRESS
```

### Configuration Variables

**municipality**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: renoweb_dk
      args:
        municipality: Esbjerg
        address: Torvegade 3, 6700 Esbjerg
```

## How to get the source arguments

Use the name of your municipality as `municipality` (e.g. `Esbjerg`, `Aalborg`, `Rødovre`) and your address as `address`, e.g. `Torvegade 3, 6700 Esbjerg` or just `Torvegade 3`. Only municipalities served by RenoWeb's public API are supported: aabenraa, aalborg, billund, bornholm, brondby, bronderslev, dragoer, egedal, esbjerg, fredensborg, gentofte, glostrup, hjorring, jammerbugt, kerteminde, mariagerfjord, randers, rodovre, samsoe, sonderborg, svendborg, varde, vordingborg.

# Stavanger Kommune, Norway

Support for schedules provided by [Stavanger Kommune, Norway](https://www.stavanger.kommune.no/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stavanger_no
      args:
        id: ID
        municipality: municipality
        gnumber: gnumber
        bnumber: bnumber
        snumber: snumber
```

### Configuration Variables

**id**  
*(string) (required)*

**municipality**  
*(string) (required)*

**gnumber**  
*(string) (required)*

**bnumber**  
*(string) (required)*

**snumber**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stavanger_no
      args:
        id: "57bf9d36-722e-400b-ae93-d80f8e354724"
        municipality: "Stavanger"
        gnumber: "57"
        bnumber: "922"
        snumber: "0"
```

## How to get the source arguments

Visit the [Stavanger Kommune, Norway](https://www.stavanger.kommune.no/renovasjon-og-miljo/tommekalender/finn-kalender/) page and search for your address.
use the parameters for url 

## Example URL

https://www.stavanger.kommune.no/renovasjon-og-miljo/tommekalender/finn-kalender/show?id=afe76cc0-19a9-4345-99bc-920bd16ab7cc&municipality=Stavanger&gnumber=58&bnumber=968&snumber=0

extract the arguments from this url you get. in this example

**id**=afe76cc0-19a9-4345-99bc-920bd16ab7cc
**municipality**=Stavanger
**gnumber**=58
**bnumber**=968
**snumber**=0

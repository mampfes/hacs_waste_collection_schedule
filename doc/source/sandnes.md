# Sandnes Kommune, Norway

Support for schedules provided by [Sandnes Kommune, Norway](https://www.sandnes.kommune.no/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sandnes_no
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
    - name: sandnes_no
      args:
        id: "181e5aac-3c88-4b0b-ad46-3bd246c2be2c"
        municipality: "Sandnes kommune 2020"
        gnumber: "62"
        bnumber: "281"
        snumber: "0"
```

## How to get the source arguments

Visit the [Stavanger Kommune, Norway](https://www.hentavfall.no/rogaland/sandnes/tommekalender) page and search for your address.
use the parameters for url 

## Example URL

https://www.hentavfall.no/rogaland/sandnes/tommekalender/finn-kalender/show?id=181e5aac-3c88-4b0b-ad46-3bd246c2be2c&municipality=Sandnes%20kommune%202020&gnumber=62&bnumber=281&snumber=0

Extract the arguments from this url you get. In this example

**id**=181e5aac-3c88-4b0b-ad46-3bd246c2be2c
**municipality**=Sandnes kommune 2020
**gnumber**=62
**bnumber**=281
**snumber**=0

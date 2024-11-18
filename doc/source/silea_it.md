# Silea SpA

Support for schedules provided by [Silea SpA](https://www.sileaspa.it), serving multiple municipalities in Italy/Lombardia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: silea_it
      args:
        municipality: MUNICIPALITY (comune)
	address: ADDRESS (street name)
```

### Configuration Variables

**municipality**  
*(String) (required)* 

**area**  
*(string) (required)* Generically starts with 'via' or 'piazza'

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: silea_it
      args:
        municipality: Lomagna
        address: via Martiri
```

```yaml
waste_collection_schedule:
    sources:
    - name: silea_it
      args:
        municipality: Calolzio
        address: via foscolo
```

## How to get the source argument

The municipality name and street address are checked against [Silea SpA](https://www.sileaspa.it) database. The extensions tries to match also partial name (i.e "Annone' matches 'Annone Brianza'). Please consider to check your address in [here](https://www.sileaspa.it/calendario-raccolta-rifiuti) in case of problems.

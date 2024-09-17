# eko-tom.pl 

Support for schedules provided by [eko-tom.pl](https://eko-tom.pl/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eko_tom_pl
      args:
        city: Czerwonak         # Enter the name of your city or village
        street: Źródlana        # If there is no street, enter the village name
        nr: 39                  # Enter the house number, check the correct nr of your home at eko-tom.pl/harmonogramy-odbiorow/
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**nr**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: eko_tom_pl
      args:
        city: MUROWANA GOŚLINA
        street: MODRZEWIOWA
        nr: 1/, 2, 3, 4, 5, 6, 7, 8, 9, 10
```

```yaml
waste_collection_schedule:
  sources:
    - name: eko_tom_pl
      args:
        city: BIAŁĘŻYN
        street: BIAŁĘŻYN
        nr: 1/A
```

## How to get the source argument

Open [eko-tom.pl](https://eko-tom.pl/harmonogramy-odbiorow/) and select your adress from the dropdown menu. "Typ Lokalizacji:" and "Typ Zabudowy:" are pointless.
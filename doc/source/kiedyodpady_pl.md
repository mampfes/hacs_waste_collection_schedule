# Kiedy Odpady (kiedyodpady.pl)

Support for schedules provided by [Kiedy Odpady (kiedyodpady.pl)](https://kiedyodpady.pl).

Source for Polish municipalities using the kiedyodpady.pl (mOdpady / mMieszkaniec) waste collection platform.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kiedyodpady_pl
      args:
        municipality: MUNICIPALITY
        city: CITY
        street: STREET
        number: NUMBER
        lookahead_days: LOOKAHEAD_DAYS
```

### Configuration Variables

**municipality**  
*(string) (required)*

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

**number**  
*(string) (optional)*

**lookahead_days**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kiedyodpady_pl
      args:
        municipality: wieliczka
        city: Wieliczka (miasto)
        street: ul. Adama Asnyka
        number: "pozosta\u0142e"
```

## How to get the source arguments

Open https://{municipality}.kiedyodpady.pl (e.g. https://pabianice.kiedyodpady.pl) and step through the address selection. The municipality is the subdomain prefix (everything before `.kiedyodpady.pl`). Copy the city, street and house number exactly as displayed in the dropdown lists; street and house number are optional for some localities.

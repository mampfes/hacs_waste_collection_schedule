# Nem Affaldsservice (Københavns Kommune)

Support for schedules provided by [Nem Affaldsservice (Københavns Kommune)](https://nemaffaldsservice.kk.dk).

Source for Nem Affaldsservice, the waste collection schedule service of Københavns Kommune (City of Copenhagen), Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nemaffaldsservice_kk_dk
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
    - name: nemaffaldsservice_kk_dk
      args:
        address: "N\xF8rrebrogade 10"
```

## How to get the source arguments

Enter your address exactly as it appears in Denmark, e.g. 'Nørrebrogade 10'. You can verify the spelling by typing your street and house number into the search box on https://nemaffaldsservice.kk.dk/ - if the site offers your address as an autocomplete suggestion, that exact text is what should be used here. If the address cannot be found, the resulting error message will list similar addresses to help you find the correct spelling.

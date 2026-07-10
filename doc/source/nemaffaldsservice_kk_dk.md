# Nem Affaldsservice (Københavns Kommune)

Support for schedules provided by [Nem Affaldsservice](https://nemaffaldsservice.kk.dk), the waste collection schedule service of Københavns Kommune (City of Copenhagen), Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nemaffaldsservice_kk_dk
      args:
        address: Nørrebrogade 10
```

### Configuration Variables

**address**  
_(String) (required)_

Street name and house number, e.g. `Nørrebrogade 10`. Must match an address served by Københavns Kommune / Nem Affaldsservice.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: nemaffaldsservice_kk_dk
      args:
        address: Nørrebrogade 10
```

## How to get the address argument

Enter your address exactly as it appears in Denmark, e.g. `Nørrebrogade 10`. You can verify the spelling by typing your street and house number into the search box on [nemaffaldsservice.kk.dk](https://nemaffaldsservice.kk.dk/) - if the site offers your address as an autocomplete suggestion, that exact text is what should be used here. If the address cannot be found, the resulting error message will list similar addresses to help you find the correct spelling.

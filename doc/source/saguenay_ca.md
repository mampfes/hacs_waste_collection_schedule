# Ville de Saguenay

Support for schedules provided by [Ville de Saguenay](https://ville.saguenay.ca).

Source for ville.saguenay.ca waste collection calendar

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: saguenay_ca
      args:
        batiment: BATIMENT
```

### Configuration Variables

**batiment**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: saguenay_ca
      args:
        batiment: 8773
```

## How to get the source arguments

1. Go to https://ville.saguenay.ca/services-aux-citoyens/environnement/horaire-des-collectes 2. Open your browser's developer tools (F12) and go to the Network tab 3. Enter your address in the search field 4. Look for a request named 'collectesinfos' (URL: https://ville.saguenay.ca/ajax/collectes/collectesinfos) 5. In the Payload tab, copy the value of 'cle_batiment' 6. Use this number as the batiment parameter

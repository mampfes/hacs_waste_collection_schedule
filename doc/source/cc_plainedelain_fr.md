# Communauté de Communes de la Plaine de l'Ain

Support for schedules provided by [Communauté de Communes de la Plaine de l'Ain](https://cc-plainedelain.fr).

Source for the collection calendars of the Communauté de Communes de la Plaine de l'Ain (CCPA), France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cc_plainedelain_fr
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cc_plainedelain_fr
      args:
        municipality: Meximieux OUEST
```

## How to get the source arguments

Enter your commune exactly as it is listed on https://cc-plainedelain.fr/les-services/gerer-vos-dechets/les-calendriers-de-collecte/ (for example 'Ambronay', 'Meximieux OUEST' or 'Meximieux SUD et EST'). Case, accents and hyphens are ignored.

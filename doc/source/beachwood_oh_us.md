# City of Beachwood, OH

Support for schedules provided by [City of Beachwood, OH](https://www.beachwoodohio.com/226/Rubbish-Recycling-More).

Source for City of Beachwood (OH, USA) residential rubbish and recycling.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: beachwood_oh_us
      args:
        street_base: STREET_BASE
        street_qualifier: STREET_QUALIFIER
```

### Configuration Variables

**street_base**  
*(string) (optional)*

**street_qualifier**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: beachwood_oh_us
      args:
        street_base: Beacon Drive
        street_qualifier: ''
```

## How to get the source arguments

Check your collection day in the <a href="https://www.beachwoodohio.com/DocumentCenter/View/4553/Rubbish-Pick-Up-Days--By-Street" target="_blank">Rubbish Pick Up Days (PDF)</a> published by the City of Beachwood. Select your street and submit. Most streets need nothing more; a few are split into sections with different days, and for those a second dropdown then asks which section matches your address.

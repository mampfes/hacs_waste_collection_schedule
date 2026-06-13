# Abfallwirtschaftsbetrieb LK Mainz-Bingen (Deprecated)

This source is deprecated and kept for existing configurations. Please use [KAW Mainz und Mainz-Bingen AöR](./kaw_mainz_bingen_de.md) for new setups.

Existing `awb_mainz_bingen_de` configurations use the current [KAW Abfallkalender](https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender) internally.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: awb_mainz_bingen_de
          args:
            bezirk: Abfuhrbezirk
            ort: Ort

```

### Configuration Variables

**bezirk**  
*(String) (required)*

**ort**  
*(String) (required)*

**strasse**  
*(String) (optional, legacy parameter; ignored by the current website)*

## Example

```yaml
waste_collection_schedule:
    sources:
        - name: awb_mainz_bingen_de
          args:
            bezirk: Stadt Ingelheim
            ort: Ingelheim Süd

```

## How to get the source argument

Find the parameters using [the KAW Abfallkalender](https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender). Select your `Abfuhrbezirk` and `Ort` and copy the names exactly.

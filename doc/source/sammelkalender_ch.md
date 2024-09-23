# Sammelkalender.ch

Support for schedules provided by [Sammelkalender.ch](https://info.sammelkalender.ch), serving multiple regions in Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sammelkalender_ch
      args:
        service_provider: SERVICE PROVIDER
        municipality: MUNICIPALITY (Gemeinde)
        street: STREET (Straße)
        hnr: HOUSE NUMBER (Hausnummer)   
```

### Configuration Variables

**service_provider**  
*(String) (required)*

**municipality**  
*(String) (required)*

**street**  
*(String) (optional)* only required if the form asks for it

**hnr**
*(String) (optional)* only required if the form asks for it

Supported service providers are:

- zeba: https://www.zebazug.ch
- zkri: https://zkri.ch
- real_luzern: https://www.realluzern.ch
- zaku: https://www.zaku.ch

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sammelkalender_ch
      args:
        service_provider: zeba
        municipality: Baar
        street: Aberenrain
```

## How to get the source argument

You can check if your parameters work by visiting the website of the service provider and entering your address. Or using the app:

- [IOS AppStore](https://apps.apple.com/ch/app/sammelkalender/id1502137213?l)
- [Android PlayStore](https://play.google.com/store/apps/details?id=ch.sammelkalender.app2020)

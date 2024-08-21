# DEPRECATED Chiltern Area - Buckinghamshire Council

This integration is deprecated and may be removed in a future release. Please use the [Itouchvision Source using the encrypted API](/doc/source/iapp_itouchvision_com.md) instead.


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: chiltern_gov_uk # DEPRECATED USE iapp_itouchvision_com INSTEAD with mun
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: chiltern_gov_uk # DEPRECATED USE iapp_itouchvision_com INSTEAD
      args:
        uprn: 200000811701
```
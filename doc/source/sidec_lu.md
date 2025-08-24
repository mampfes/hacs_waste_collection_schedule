# SIDEC

Support for SIDEC waste collections.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: sidec_lu
      args:
        commune: MUNICIPALITY
```

### Arguments

**commune**  
*(string) (required)*

The name of your municipality (`commune`).

This will be a dropdown menu in the Home Assistant UI, so you can simply select your municipality from the list.
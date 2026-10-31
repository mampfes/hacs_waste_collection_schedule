# Lozzolo, Roasio (COVEVAR)

Support for schedules provided by [Lozzolo, Roasio (COVEVAR)](https://www.comune.roasio.vc.it).

Source for the COVEVAR door-to-door collection calendar of Lozzolo and Roasio (Vercelli).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lozzolo_roasio_it
      args:
        utenza: UTENZA
```

### Configuration Variables

**utenza**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lozzolo_roasio_it
      args:
        utenza: non domestica
```

## How to get the source arguments

Lozzolo and Roasio share one calendar, read from the yearly 'Calendario Raccolta Rifiuti' notice on Roasio's website; no address is needed. Households keep `utenza` at `domestica`; businesses choose `non domestica` to add the non-domestic residual waste, commercial metals and commercial cardboard rounds. Sanitary textiles (tessili sanitari) and garden waste (sfalci verdi) are only collected for users who have signed up with COVEVAR.

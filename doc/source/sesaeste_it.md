# S.E.S.A.

Support for schedules provided by [S.E.S.A. S.p.A.](https://sesaeste.it), serving municipalities in the province of Padova, Italy.

The source replays the traffic of the official S.E.S.A. mobile app, so it returns the same calendar the app shows.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sesaeste_it
      args:
        user_municipality: MUNICIPALITY
```

### Configuration Variables

**user_municipality**
*(string) (required)*

The name of your municipality, spelled as it appears in the municipality list of the S.E.S.A. app.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sesaeste_it
      args:
        user_municipality: Legnaro
```

## How to get the source argument

1. Open the S.E.S.A. app or <https://app.sesaeste.it/?p=new-indirizzo> in a browser.
2. Open the municipality picker and find your municipality.
3. Use that name as `user_municipality`, for example `Legnaro`, `Solesino` or `Polverara`.

A partial name is accepted as long as it matches exactly one municipality. If it matches several, the error message lists the candidates so you can pick one.

## Notes

- Only the municipality is needed. S.E.S.A. publishes one calendar per municipality, not per street.
- The waste types come back in Italian (`Secco`, `Umido`, `Carta`, `Vetro`, `Verde`, `Plastica lattine`). Use the `customize` option if you would rather see different labels.
- `app.sesaeste.it` serves an incomplete TLS certificate chain, so this source skips certificate verification. Browsers and Android hide the problem by fetching the missing intermediate certificate themselves.

# Innherred Renovasjon

Support for schedules provided by [Innherred Renovasjon](https://ir.nt.no) located in Trøndelag, Norway.
The following municipalities are covered by this provider:
- Frosta
- Inderøy
- Levanger
- Malvik
- Meråker
- Selbu
- Stjørdal
- Tydal
- Verdal

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: irnt_no
      args:
        premise_id: 5779878e-e9e2-4019-8f0d-d4b132356077
```

### Configuration Variables

**premise_id**
*(string) (required)*


#### How to retrieve the `premise_id` value

The `premise_id` needs to be looked up at innherredrenovasjon.no:

1. Open [Tømmeplan](https://innherredrenovasjon.no/tommeplan/)
2. Type your address in the search field
3. Click on the correct address
4. Copy the string after "`tommeplan/`" from the URL; this is your `premise_id`

Alternatively you can search for your address using the following web API URL:
https://innherredrenovasjon.no/wp-json/ir/v1/addresses/Min%20Gate%2044

`premise_id` equals to `id` in the returned JSON result.


### Types returned

The following waste types will be returned:
* Restavfall
* Papp/papir
* Matavfall
* Plastemballasje
* Glass- og metallemballasje

Use `sources.customize` to filter or rename the waste types:

```yaml
waste_collection_schedule:
  sources:
    - name: irnt_no
      args:
        premise_id: 5779878e-e9e2-4019-8f0d-d4b132356077
      calendar_title: Avfallskalender
      customize:
        # rename types to shorter name
        - type: Glass- og metallemballasje
          alias: Glass&metall

        # hide unwanted types
        - type: Plastemballasje
          show: false
```
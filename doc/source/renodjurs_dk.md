## Reno Djurs I/S

Support for schedules provided by [Reno Djurs i/s](https://renodjurs.dk/), serving Odder and Skanderborg kommuner, Denmark.

## Configuration via configuration.yaml

```plaintext
waste_collection_schedule:
    sources:
    - name: renodjurs_dk
      args:
        id: See description
```

### Configuration Variables

id  
_(String) (required)_

## Example

```plaintext
waste_collection_schedule:
    sources:
    - name: renodjurs_dk
      args:
        id: "45000"
```

## How to get the id

Go to the [Min Side Reno Djurs I/S](https://minside.renodjurs.dk/) page, enter your addres.

In the URL (web page address) copy the number after `id=`

`I.e.` [`https://minside.renodjurs.dk/Ordninger.aspx?id=45000`](https://minside.renodjurs.dk/Ordninger.aspx?id=45000)

Then it's the `45000` part used in the integration
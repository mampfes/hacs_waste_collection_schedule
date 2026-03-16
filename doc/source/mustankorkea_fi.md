# Mustankorkea

Support for past and upcoming pick ups provided by [Oma Mustankorkea](https://oma.mustankorkea.fi/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: mustankorkea_fi
      args:
        username: "YOUR_USERNAME"
        password: "YOUR_PASSWORD"
        contract_id: "YOUR_CONTRACT_ID"
```

### Configuration Variables

**username**
*(string) (required)*

**password**
*(string) (required)*

**contract_id**
*(string)*


## How to get the source arguments

**You need to have a registered account in Mustankorkea's self-service portal!**
To register one, you need to have a waste collection contract. Press "Luo tunnukset" at oma.mustankorkea.fi and follow the instructions.

If you have more than one contract (i.e. collection address), you also need to specify the contract_id in configuration.
To find it, log in and select your contract from the list. Check the URL of your web browser, should be something like:
`https://oma.mustankorkea.fi/e-services/mustankorkea/emptying-infos/30-00012345-00`
Your contract id is the last bit after the final slash, e.g. 30-00012345-00
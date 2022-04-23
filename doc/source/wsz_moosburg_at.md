# WSZ-Moosburg.at

Support for schedules provided by [wsz-moosburg.at](https://wsz-moosburg.at).

## Configuration via configuration.yaml

There are two options to configure this source.

### Using the Address ID

```yaml
waste_collection_schedule:
  sources:
    - name: wsz_moosburg_at
      args:
        address_id: ID
```

#### Configuration Variables

**address_id**<br>
*(integer) (required)* See the next section on how to obtain it.

#### How to get the Address ID

For this you will have to use a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open [https://wsz-moosburg.at/calendar](https://wsz-moosburg.at/calendar).
2. Open the Developer Tools (Ctrl + Shift + I / Cmd + Option + I) and open the `Network` tab.
3. Select your `Gemeinde` from the list.
4. Select your `Addresse` from the list.
5. There might be another step to select your `Straße`, but this depends on the address. If it's prompted to you, select that as well.
6. Select the last entry in the `Network` tab's list, it should be a number followed by `?include-public-holidays`, e.g. `69980?include-public-holidays`.
7. This number (e.g. `69980`) is what needs to be used as `address_id` in the configuration.

### Using the full Address

```yaml
waste_collection_schedule:
  sources:
    - name: wsz_moosburg_at
      args:
        municipal: Gemeinde
        address: Adresse
        street: Straße
```

#### Configuration Variables

Please note that exact spelling and casing matters.

**municipal**<br>
*(string) (required)*

**address**<br>
*(string) (required)*

**street**<br>
*(string) (required)*

#### How to get the correct Address

In any web browser:

1. Open [https://wsz-moosburg.at/calendar](https://wsz-moosburg.at/calendar).
2. Select your `Gemeinde` from the list. This is the value for `municipal`.
3. Select your `Addresse` from the list. This is the value for `address`.
4. There might be another step to select your `Straße`, but this depends on the address. 
    - If it's prompted to you, select that as well. This is the value for `street`.
    - If it is not prompted, use the same value for `address` also for `street`.

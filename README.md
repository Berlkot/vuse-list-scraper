# Universities list scraper
Scrapes universities for data analysis of applicants stats
- [x] Get requests
- [x] Post requests
- [x] Adding columns
- [x] Per-request parameters
- [x] Statistical analysis
- [x] Rate-limiting
- [ ] Data filtering
- [ ] Error handling
- [ ] Reading data outside table
---
### Technical notes
- Reading more than 2 tables may confuse parser
- Sometimes it is required to debug table values manually to retrieve data indices

## Requirements
- python 3.11
- aiohttp
- bs4
---
# Config guide

## Adding new table
Any new university site is required to be added to `"url_mapping"` and `"site_specials"`.

The `"url_mapping"` section contains table URLs and query parameters surrounded with `[]`.   
#### Example:
```json
"url_mapping": {
  "university_site": [
    [
      "table_link",
      {
        "post_data": "data"
      },
      {
        "headers": "headers"
        "any_other_aiohttp_parameter": "any_other_aiohttp_parameter"
      }
    ]
  ]
},
```
> **The order here matters. Link goes first then post data (It is required to be there if you have any query parameters even in GET. You can replace it with `""`) and finally parameters in `{}`**

The `"site_specials"` section contains request type, site specific true and false and data columns indices.
Data columns are called with `"track_values"`. If no column wasn't found, output table will receive `"Err: N/A"` value.

#### Example:
```json
"site_specials": {
  "university_site": {
    "request_type": "GET",
    "true": "да",
    "false": "нет",
    "column_1": 0,
    "column_2": 1,
    "column_3": 2,
    "column_4": 3
  }
```
## Naming links
To replace raw URL wth beautiful custom name, place it to `"url_masking"`
> **Naming goes for ALL links fed into program from up to down. If you don't want to name any link fill its place with `""`**
#### Example:
```json
"url_masking":[
  "name",
  "",
  "name",
  "man.......eman",
  ""
]
```
## Compute columns
To make program to compute sum, average, max, min add matching `"track_values"` index to `"compute_sum"`, `"compute_average"`, `"compute_max"`, `"compute_min"` respectively.
### Naming compute names
Same logic as in naming links, except here you should place names to `"compute_names"`
### Disabling Compute
To disable compute columns set `"compute"` to `false`


## Rate-limiting
Program has per-domain rate-limiting feature
### Setting rate-limit time
To set rate-limit time change default `"ratelimit_value"` to any number of seconds you want to wait for
### Disabling Rate-limiting
To disable rate-limiting columns set `"ratelimit_requests"` to `false`

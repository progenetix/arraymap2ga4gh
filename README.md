# Implementation of the [GA4GH](http://github.com/ga4gh/schemas/) schema based on genome profiles and metadata from [arrayMap](http://arraymap.org)

This repository will contain data and information regarding the [arrayMap](http://arraymap.org) based implementation of a GA4GH schema structure. While it is not expected that GA4GH compliant resources mirror the schema in their internal structure, this project is aimed at showing the principle feasibility of such an approach, mainly to test & drive schema development.

Data & schemas represented here are not kept in a stable/versioned status, but are updated together with or anticipating GA4GH schema changes.

Structure:

* data: JSON dumps of data from the arraymap2ga4gh conversion of arrayMap collections (subsets)
* examples: JSON-nice single/few selected records (biosamples, variants ...) etc. to show value encodings...

### How to Use the data

The data is in JSON format, you can use MongoDB for easy import and manipulation

The download and installation instructions of the community version of MongoDB can be found [here](https://www.mongodb.com/download-center#community).

Each zip file contains not only the demo data in json, but also a shell script to import the data into json.
You can simply run:
```
sh importdb.sh
```

To query from MongoDB shell
```
use test
db.biosamples.find({'attributes.country.values.string_value' : 'United Kingdom'})
db.biosamples.findOne({'description' : {'$regex' : 'breast'}})
db.variants.find({alternate_bases:"DEL", reference_name:"17", start:{$gte:30000000}, end:{$lte:31000000}},{"calls.call_set_id":1})
```

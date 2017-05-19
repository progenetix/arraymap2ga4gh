# Implementation of the [GA4GH](http://github.com/ga4gh/schemas/) schema based on genome profiles and metadata from [arrayMap](http://arraymap.org)

This repository will contain data and information regarding the [arrayMap](http://arraymap.org) based implementation of a GA4GH schema structure. While it is not expected that GA4GH compliant resources mirror the schema in their internal structure, this project is aimed at showing the principle feasibility of such an approach, mainly to test & drive schema development.

Data & schemas represented here are not kept in a stable/versioned status, but are updated together with or anticipating GA4GH schema changes.

Structure:

* data: JSON dumps of data from the arraymap2ga4gh conversion of arrayMap collections (subsets)
* examples: JSON-nice single/few selected records (biosamples, variants ...) etc. to show value encodings...
* tools: scripts for manipulating the test data and providing e.g. servers side implementations

### How to import the data

The data is in JSON format, you can use MongoDB for easy import and manipulation

The download and installation instructions of the community version of MongoDB can be found [here](https://www.mongodb.com/download-center#community).

Each zip file contains not only the demo data in json, but also a shell script to import the data into json.
You can simply run:
```
sh importdb.sh
```

### Data manipulation with MongDB shell

To query from MongoDB shell
```
use test
db.biosamples.find({'attributes.country.values.string_value' : 'United Kingdom'})
db.biosamples.findOne({'description' : {'$regex' : 'breast'}})
db.variants.find({variant_type:"DEL", reference_name:"17", start:{$gte:30000000}, end:{$lte:31000000}},{"calls.call_set_id":1})
```

### Data manipulation with Python

In the tools directory, IPython/Jupyter notebooks are provided for exploring the datasets and -structures.

The instruction for installing _Jupyter_ can be found [here](https://jupyter.org/install.html)

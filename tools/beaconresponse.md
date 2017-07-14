## BeaconResponse - a Perl CGI for Beacon+ queries on GA4GH compatible databases

### Query parameters

* dataset_id
   * the dataset to be queried
   * example: `arraymap`, which will expand to `arraymap_ga4gh` as database name
   * default: `arraymap`
* assembly_id
   * the genome assembly
   * example: `GRCh36`
   * by default, the `assembly_id` (in lower case) is part of the variants and callsets collections' names (see below)

### Database naming

The script uses some naming conventions for databases and collections:

* `db` (as a MongoDB database)
   * `dataset_id`_ga4gh
* collections
   * `individuals`
   * `biosamples`
   * `callsets`_`assembly_id` (e.g. *callsets_grch36*)
   * `variants`\_scope\_`assembly_id` (e.g. *variants_cnv_grch36*)


### Example use, command line:

The first examples are CNV requests:

```
perl beaconresponse.cgi variants.reference_name=chr9 variants.variant_type=DEL variants.start_min=20000000 variants.start_max=21984490 variants.end_min=21984490 variants.end_max=25000000 biosamples.bio_characteristics.ontology_terms.term_id=NCIT:C3058

perl beaconresponse.cgi variants.reference_name=9 variants.variant_type=DEL variants.start_min=19000000 variants.start=21984490 variants.end_min=21984490 variants.end_max=25000000 biosamples.bio_characteristics.ontology_terms.term_id=PGX:ICDOT:C719 dataset_ids=dipg
```

This query is a standard SNV query:

```
perl beaconresponse.cgi variants.reference_name=17 variants.alternate_bases=C variants.start=7578535 biosamples.bio_characteristics.ontology_terms.term_id=PGX:ICDOT:C717 dataset_ids=dipg
```

### Example use, web call:

SNV query on dataset "dipg" with phenotype response:

* http://progenetix.org/beacon/query/?variants.reference_name=17&variants.reference_bases=G&variants.alternate_bases=A&variants.start=7577121&dataset_ids=dipg&phenotypes=1

CNV query on dataset "dipg", with phenotype response:

* http://progenetix.org/beacon/query/?variants.reference_name=9&variants.variant_type=DEL&variants.start_min=19000000&variants.start_max=21984490&variants.end_min=21984490&variants.end_max=25000000&dataset_ids=dipg&phenotypes=1

CNV query (defaults do dataset "arraymap") with bio-metadata component and phenotype response:

* http://progenetix.org/beacon/query/?variants.reference_name=chr9&variants.variant_type=DEL&variants.start_min=20000000&variants.start_max=21984490&variants.end_min=21984490&variants.end_max=25000000&biosamples.bio_characteristics.ontology_terms.term_id=NCIT:C3058&biosamples.bio_characteristics.ontology_terms.term_id=NCIT:C3059&phenotypes=1

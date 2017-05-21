### Example use, command line:

TODO:
* use canonical names for collections, so tat the API can provide information about the resource's content (e.g. `variants_cnv_grch36`)


```
perl beaconresponse.cgi variants.reference_name=chr9 variants.variant_type=DEL variants.start=20000000 variants.start=21984490 variants.end=21984490 variants.end=25000000 biosamples.bio_characteristics.ontology_terms.term_id=NCIT:C3058
```

```
perl beaconresponse.cgi variants.reference_name=9 variants.variant_type=DEL variants.start=19000000 variants.start=21984490 variants.end=21984490 variants.end=25000000 biosamples.bio_characteristics.ontology_terms.term_id=PGX:ICDOT:C719 db=dipg_ga4gh varcoll=variants_cnv_grch36 callsetcoll=callsets_cnv_grch36
```

```
perl beaconresponse.cgi variants.reference_name=17 variants.alternate_bases=C variants.start=7578535 biosamples.bio_characteristics.ontology_terms.term_id=PGX:ICDOT:C717 db=dipg_ga4gh varcoll=variants_maf_grch36 callsetcoll=callsets_maf_grch36
```

### Example use, web call:

```
http://arraymap.org/beaconresponse/?variants.reference_name=chr9&variants.variant_type=DEL&variants.start=20000000&variants.start=21984490&variants.end=21984490&variants.end=25000000&biosamples.bio_characteristics.ontology_terms.term_id=NCIT:C3058&biosamples.bio_characteristics.ontology_terms.term_id=NCIT:C3059
```

```
http://arraymap.org/beaconresponse/?variants.reference_name=9&variants.variant_type=DEL&variants.start=19000000&variants.start=21984490&variants.end=21984490&variants.end=25000000&biosamples.bio_characteristics.ontology_terms.term_id=PGX:ICDOT:C719&db=dipg_ga4gh&varcoll=variants_cnv_grch36&callsetcoll=callsets_cnv_grch36
```

```
http://arraymap.org/beaconresponse/?variants.reference_name=17&variants.alternate_bases=C&variants.start=7578535&biosamples.bio_characteristics.ontology_terms.term_id=PGX:ICDOT:C717&db=dipg_ga4gh&varcoll=variants_maf_grch36&callsetcoll=callsets_maf_grch36
```

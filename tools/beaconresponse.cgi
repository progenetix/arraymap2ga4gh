#!/usr/bin/perl

# Progenetix & arrayMap site scripts
# © 2000-2017 Michael Baudis: m@baud.is

use strict;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw(param);

use JSON;
use MongoDB;
use MongoDB::MongoClient;
use Data::Dumper;

=pod

Please see the associated beaconresponse.md
=cut

my $datasetPar  =   _getDatasetParams();

# GA4GH variant attributes

my $varQpar     =   _getVariantParams();
$varQpar        =   _normVariantParams($varQpar);
my $varQ        =   _createVariantQuery($varQpar);

my $biosQpar    =   _getBiosampleParams();
my $biosQ       =   _createBiosampleQuery($biosQpar);

# catching input errors #######################################################

# TODO: expand ...
my $errorM      =   _checkParameters($varQpar);

my $queryScope  =   'datasetAlleleResponses';
my $queryType   =   'alleleRequest';
if (param('variants.variant_type') =~ /^D(?:UP)|(?:EL)$/i) {
  $queryType    =   'CNVrequest';
  $queryScope   =   'datasetCNVresponses';
  $datasetPar->{varcoll}  =~  s/_alleles_/_cnv_/;
  $datasetPar->{callsetcoll}  =~  s/_alleles_/_cnv_/;
}

###############################################################################

my $counts      =   {};
my $dbCall;             # recyclable
my $dbconn      =   MongoDB::MongoClient->new()->get_database( $datasetPar->{db} );

=pod

The ids of biosamples matching (designated) metadata criteria are retrieved. This can be, as in the first example, biosamples with an "characteristic" containing a specific ontology term.

=cut

# getting the number of all biosamples in the collection
$dbCall         =   $dbconn->run_command({"count" => $datasetPar->{samplecoll}});

$counts->{bs_all}       =   $dbCall->{n};

# getting and  counting the ids of all biosamples which match the biosample query
$dbCall         =   $dbconn->run_command([
                      "distinct"  =>  $datasetPar->{samplecoll},
                      "key"       =>  'id',
                      "query"     =>  $biosQ,
                    ]);
my $biosampleIds        =   $dbCall->{values};
$counts->{bs_matched}   =   scalar(@{ $biosampleIds });

###############################################################################

# counting all variants in the variant collection
$dbCall         =   $dbconn->run_command({"count" => $datasetPar->{varcoll}});
$counts->{var_all}      =   $dbCall->{n};

# counting all callsets with any variant
$dbCall         =   $dbconn->run_command([
                      "distinct"  =>  $datasetPar->{varcoll},
                      "key"       =>  'calls.call_set_id',
                      "query"     =>  {},
                    ]);
$counts->{cs_all}     =   scalar(@{ $dbCall->{values} });

# getting and  counting all callset ids with matching variants
$dbCall         =   $dbconn->run_command([
                      "distinct"  =>  $datasetPar->{varcoll},
                      "key"       =>  'calls.call_set_id',
                      "query"     =>  $varQ,
                    ]);
my $callsetIds          =   $dbCall->{values};
$counts->{cs_matched}   =   scalar(@{ $callsetIds });

###############################################################################

# getting and counting all biosample ids from those callsets,
# which are both fulfilling the biosample metadata query and are listed
# in the matched callsets

my $bsQvarQmatchedQ   =   {};
my @bsQvarQlist       =   ();
my $csBiosampleIds    =   [];

if (grep{ /.../ } keys %{ $biosQ } ) {
  push(@bsQvarQlist, { biosample_id => { '$in' => $biosampleIds } } );
}
if (grep{ /.../ } keys %{ $varQ } ) {
  push(@bsQvarQlist, { id => { '$in' => $callsetIds } } );
}

if (@bsQvarQlist > 1) {
  $bsQvarQmatchedQ      =   { '$and' => [ @bsQvarQlist ] };
} elsif (@bsQvarQlist == 1) {
  $bsQvarQmatchedQ      =   @bsQvarQlist[0];
}
# sanity check; if biosample query but no ids => no natch
if (
  (grep{ /.../ } keys %{ $biosQ } )
  &&
  ($counts->{bs_matched} < 1)
) {

  $csBiosampleIds       =   [];

} else {

  $dbCall       =   $dbconn->run_command([
                      "distinct"  =>  $datasetPar->{callsetcoll},
                      "key"       =>  'biosample_id',
                      "query"     =>  $bsQvarQmatchedQ,
                    ]);
  $csBiosampleIds     =   $dbCall->{values};

}

$counts->{bs_var_matched} =   scalar(@{ $csBiosampleIds });

###############################################################################

# TODO: The response has to be extended and also to be adapted to the "Dataset" option.
my $beaconResponse      =   {
  beaconId              =>  "arraymap-beacon",
  $queryType            =>  $varQ,
  biosampleRequest      =>  $biosQ,
  $queryScope           =>  1 * $counts->{bs_var_matched},
  frequency             =>  1* (sprintf "%.4f",  $counts->{bs_var_matched} / $counts->{bs_all}),
  callCount             =>  $counts->{cs_matched},
  sampleCount           =>  1 * $counts->{bs_var_matched},
  error                 =>  $errorM,
  info                  =>  'The query was against database "'.$datasetPar->{db}.'", variant collection "'.$datasetPar->{varcoll}.'". '.$counts->{cs_matched}.' / '.$counts->{cs_all}.' matched callsets for '.$counts->{var_all}.' variants. Out of '.$counts->{bs_all}.' biosamples in the database, '.$counts->{bs_matched}.' matched the biosample query; of those, '.$counts->{bs_var_matched}.' had the variant.',
};

if (! -t STDIN) {

  print 'Content-type: application/json'."\n\n";

}

print JSON::XS->new->pretty( 1 )->allow_blessed->convert_blessed->encode($beaconResponse);

print ."\n";

exit;


################################################################################
# SUBs #########################################################################
################################################################################

sub _getDatasetParams {

  my $qPar      =   {};

  my %defaults  =   (
    varcoll     =>  'variants_alleles',
    callsetcoll =>  'callsets_alleles',
  );

  $qPar->{samplecoll}   =   param('samplecoll');
  if ($qPar->{samplecoll} !~ /^\w{3,64}$/) { $qPar->{samplecoll} = 'biosamples' }

  $qPar->{dataset_id}   =   param('dataset_id');
  if ($qPar->{dataset_id} !~ /^\w{3,64}$/) { $qPar->{dataset_id} = 'arraymap' }
  $qPar->{db}   =   $qPar->{dataset_id}.'_ga4gh';

  $qPar->{assembly_id}   =   param('assembly_id');
  if ($qPar->{assembly_id} !~ /^\w{3,64}$/) { $qPar->{assembly_id} = 'GRCh36' }

  foreach (keys %defaults) {

    $qPar->{$_} =   param($_);
    if ($qPar->{$_} !~ /^\w{3,64}$/) { $qPar->{$_} = $defaults{$_} }
    $qPar->{$_} .=   '_'.lc($qPar->{assembly_id});

  }

  return $qPar;

}

################################################################################

sub _getBiosampleParams {

=pod

Atributes not used (yet):

=cut

  my $qPar      =   {};

  foreach (qw(
    id
    bio_characteristics.ontology_terms.term_id
  )) { $qPar->{$_}      =   [ param('biosamples.'.$_) ] }

  return $qPar;

}

################################################################################

sub _getVariantParams {

=pod

Atributes not used (yet):
  variant_set_id
  svlen
  filters_applied
  filters_passed

  cipos
  ciend

=cut

  my $qPar      =   {};

# TODO: Implement alternate_bases as list

  foreach (qw(
    id
    reference_name
    reference_bases
    alternate_bases
    variant_type
  )) { $qPar->{$_}      =   param('variants.'.$_) }

  foreach (qw(
    start
    end
  )) { $qPar->{$_}      =   [ sort {$a <=> $b } (param('variants.'.$_)) ] }

  #print Dumper $qPar;

  return $qPar;

}

################################################################################

sub _normVariantParams {

  my $qPar      =   $_[0];

  (
    $qPar->{start},
    $qPar->{end}
  )             =   _normQueryStartEnd(
                      $qPar->{start},
                      $qPar->{end}
                    );

  $qPar->{reference_name} =~  s/chr?o?//i;

  return $qPar;

}

###############################################################################

sub _normQueryStartEnd {

  # A minimum of one start base

  my ($start, $end)     =   @_;

  if ($start->[1] !~ /^\d+?$/) { $start->[1] = $start->[0] }
  if ($end->[0]   !~ /^\d+?$/) { $end->[0]   = $start->[1] }
  if ($end->[1]   !~ /^\d+?$/) { $end->[1]   = $end->[0]   }

  $start->[0]   *=  1;
  $start->[1]   *=  1;
  $end->[0]     *=  1;
  $end->[1]     *=  1;
  $start        =   [sort { $a <=> $b } @$start];
  $end          =   [sort { $a <=> $b } @$end];

  return ($start, $end);

}

################################################################################

sub _checkParameters {

  my $qPar      =   $_[0];

  my $errorM;

  if ($qPar->{start}->[0] !~ /^\d+?$/) {
    $errorM     .=    '"variants.start" did not contain a numeric value. ';
  }

  if ($qPar->{reference_name} !~ /^(?:(?:(?:1|2)?\d)|x|y)$/i) {
    $errorM     .=    '"variants.reference_name" did not contain a valid value (e.g. "chr17" "8", "X"). ';
  }

  if (
  ($qPar->{variant_type} !~ /^D(?:UP)|(?:EL)$/)
  &&
  ($qPar->{alternate_bases} !~ /^[ATGC]+?$/)
  ) {
    $errorM     .=    'There was no valid value for either "variants.variant_type" or "variants.alternate_bases".';
  }

  return $errorM;

}

################################################################################

sub _createBiosampleQuery {

  my $qPar      =   $_[0];
  my @qList;

  foreach my $qKey (keys %{$qPar}) {

    my @thisQlist;

    foreach (grep{ /.../ } @{ $qPar->{$qKey} } ) {

      push(@thisQlist, { $qKey => $_ } );

    }

=pod

Queries with multiple options for the same attribute are treated as logical "OR".

=cut

  if (@thisQlist == 1)    { push(@qList, $thisQlist[0]) }
  elsif (@thisQlist > 1)  { push(@qList, {'$or' => [ @thisQlist ] } ) }

  }

=pod

The construction of the query object depends on the detected parameters:

* if empty list => no change, empty object
* if 1 parameter => direct use
* if several parameters are queried => connection through the MongoDB  "$and" constructor

=cut

  if (@qList == 1)    { return $qList[0] }
  elsif (@qList > 1)  { return { '$and' => \@qList } }
  else                { return {} }

}

################################################################################

sub _createVariantQuery {

  my $qPar      =   $_[0];
  my $qObj      =   {};

  if ($qPar->{variant_type} =~ /^D(?:UP)|(?:EL)$/) {

    $qObj       =   {
      '$and'    => [
        { reference_name        =>  $qPar->{reference_name} },
        { variant_type          =>  $qPar->{variant_type} },
        { start =>  { '$gte'  =>  1 * $qPar->{start}->[0] } },
        { start =>  { '$lte'  =>  1 * $qPar->{start}->[1] } },
        { end   =>  { '$gte'  =>  1 * $qPar->{end}->[0] } },
        { end   =>  { '$lte'  =>  1 * $qPar->{end}->[1] } },
      ],
    };

  } elsif ($qPar->{alternate_bases} =~ /^[ATGC]+?$/) {

    $qObj       =   {
      '$and' => [
        { reference_name        =>  $qPar->{reference_name} },
        { alternate_bases       =>  $qPar->{alternate_bases} },
        { start =>  1 * $qPar->{start}->[0] },
      ],
    };

  }

  return $qObj;

}

################################################################################

1;

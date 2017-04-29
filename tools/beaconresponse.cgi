#!/usr/bin/perl

# Progenetix & arrayMap site scripts
# © 2000-2017 Michael Baudis: m@baud.is

use strict;
use CGI::Carp qw(fatalsToBrowser);
use CGI qw(param);

use JSON;
use MongoDB;
use MongoDB::MongoClient;

=pod

This script implements a Beacon-style API against a GA4GH schema compatible set of MongoDB collections. Each of these collections contains records of a GA4GH core data type. The current implementation makes use of the

	* variants
	* biosamples
	* callsets
	
...collections, where a combination of queries against a subset of of "Biosample" and "Variant" records' attributes leads to a response with count information about the mached data.

Example use, command line:

perl beaconresponse.cgi variants.reference_name=chr9 variants.variant_type=DEL variants.start=20000000 variants.start=21984490 variants.end=21984490 variants.end=25000000 biosample.bio_characteristics.ontology_terms.term_id=NCIT:C3058

Example use, as server CGI:

http://arraymap.org/beaconresponse/?variants.reference_name=chr9&variants.variant_type=DEL&variants.start=20000000&variants.start=21984490&variants.end=21984490&variants.end=25000000&biosample.bio_characteristics.ontology_terms.term_id=NCIT:C3058

=cut

#print 'Content-type: text/plain'."\n\n";

my $db								=		'arraymap_ga4gh';
my $varColl						=		'variants';
my $sampleColl				=		'biosamples';
my $varQpar						=		{};
my $varQ							=		{};
my $biosQpar					=		{};
my $biosQ							=		{};

# GA4GH variant attributes

$varQpar							=		_getVariantParams();
$varQpar							=		_normVariantParams($varQpar);
$biosQpar							=		_getBiosampleParams();

# catching input errors #######################################################

# TODO: expand ...

my $errorMessage			=		_checkParameters($varQpar);

my $counts						=		{};
my $dbCall;						# recyclable

my $dbconn						=		MongoDB::MongoClient->new()->get_database( $db );

###############################################################################

=pod

The ids of biosamples matching (designated) metadata criteria are retrieved. This can be, as in the first example, biosamples with an "characteristic" containing a specific ontology term.

=cut

$biosQ								=		_createBiosampleQuery($biosQpar);

# counting all variants
$dbCall								=		$dbconn->run_command({"count" => 'biosamples'});
$counts->{bs_all}			=		$dbCall->{n};

# getting and  counting all calsset ids with matching variants
$dbCall								=		$dbconn->run_command([
														"distinct"	=>	'biosamples',
														"key"     	=>	'id',
														"query"   	=>	$biosQ,
													]);
my $biosampleIds			=		$dbCall->{values};
$counts->{bs_matched}	=		scalar(@{ $biosampleIds });

###############################################################################

$varQ									=		_createVariantQuery($varQpar);

# counting all variants
$dbCall								=		$dbconn->run_command({"count" => 'variants'});
$counts->{var_all}		=		$dbCall->{n};

# counting all callsets with any variant
$dbCall								=		$dbconn->run_command([
														"distinct"	=>	'variants',
														"key"     	=>	'calls.call_set_id',
														"query"   	=>	{},
													]);
$counts->{cs_all}			=		scalar(@{ $dbCall->{values} });

# getting and  counting all callset ids with matching variants
$dbCall								=		$dbconn->run_command([
														"distinct"	=>	'variants',
														"key"     	=>	'calls.call_set_id',
														"query"   	=>	$varQ,
													]);
my $callsetIds				=		$dbCall->{values};
$counts->{cs_matched}	=		scalar(@{ $callsetIds });

# getting and counting all biosample ids from those callsets,
# which are both fulfilling the biosample metadata query and are listed
# in the matched callsets
$dbCall								=		$dbconn->run_command([
														"distinct"	=>	'callsets',
														"key"     	=>	'biosample_id',
														"query"   	=>	{ '$and' => [
															{ biosample_id => { '$in' => $biosampleIds } },
															{ id => { '$in' => $callsetIds } },
														]},
													]);
my $csBiosampleIds		=		$dbCall->{values};
$counts->{bs_var_matched}	=		scalar(@{ $csBiosampleIds });

###############################################################################

my $beaconResponse		=		{
	beaconId						=>	"arraymap-beacon",
	alleleRequest				=>	$varQ,
	biosampleRequest		=> 	$biosQ,
	datasetAlleleResponses	=>	$counts->{bs_var_matched},
	error								=>	$errorMessage,
	info								=>	$counts->{cs_matched}.' / '.$counts->{cs_all}.' matched callsets for '.$counts->{var_all}.' variants. Out of '.$counts->{bs_all}.' biosamples in the database, '.$counts->{bs_matched}.' matched the biosample query; of those, '.$counts->{bs_var_matched}.' had the variant.',
};

if (! -t STDIN) {

	print	'Content-type: application/json'."\n\n";

}

print	JSON::XS->new->pretty( 1 )->allow_blessed->convert_blessed->encode($beaconResponse);

print ."\n";

exit;


###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################


sub _getBiosampleParams {

=pod

Atributes not used (yet):

=cut

	my $qPar						=		{};

	foreach (qw(
		id
	)) {

			$qPar->{$_}			=		param('biosample.'.$_);

	};

	foreach (qw(
		bio_characteristics.ontology_terms.term_id
	)) {
		$qPar->{$_}				=		[ param('biosample.'.$_) ];
	};

	return $qPar;

}

###############################################################################

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

	my $qPar					=		{};

	foreach (qw(
		id
		reference_name
		reference_bases
		alternate_bases
		variant_type
	)) {
		$qPar->{$_}			=		param('variants.'.$_);
	};

	foreach (qw(
		start
		end
	)) {
		$qPar->{$_}			=		[ sort {$a <=> $b } (param('variants.'.$_)) ];
	};

	return $qPar;

}

###############################################################################

sub _normVariantParams {

	my $qPar					=		$_[0];

	(
		$qPar->{start},
		$qPar->{end}
	) 									=		_normQueryStartEnd(
														$qPar->{start},
														$qPar->{end}
													);

	$qPar->{reference_name}	=~	s/chr?o?//i;

	return $qPar;

}

###############################################################################

sub _normQueryStartEnd {

	my ($qStart, $qEnd)	=		@_;

	if ($qStart->[1] !~ /^\d+?$/)	{ $qStart->[1]	= $qStart->[0] }
	if ($qEnd->[0] !~ /^\d+?$/)		{ $qEnd->[0] 		= $qStart->[1] }
	if ($qEnd->[1] !~ /^\d+?$/)		{ $qEnd->[1] 		= $qEnd->[0] }

	$qStart->[0]				*=	1;
	$qStart->[1]				*=	1;
	$qEnd->[0]					*=	1;
	$qEnd->[1]					*=	1;
	$qStart							=		[sort { $a <=> $b } @$qStart];
	$qEnd								=		[sort { $a <=> $b } @$qEnd];

	return ($qStart, $qEnd);

}

################################################################################

sub _checkParameters {

	my $qPar						=		$_[0];

	my $errorMessage;

	if ($qPar->{start}->[0] !~ /^\d+?$/) {
		$errorMessage			.=		'"variants.start" did not contain a numeric value. ';
	}

	if ($qPar->{reference_name} !~ /^(?:(?:(?:1|2)?\d)|x|y)$/i) {
		$errorMessage			.=		'"variants.reference_name" did not contain a valid value (e.g. "chr17" "8", "X"). ';
	}

	if (
		($qPar->{variant_type} !~ /^D(?:UP)|(?:EL)$/)
		&&
		($qPar->{alternate_bases} !~ /^[ATGC]+?$/)
	) {
		$errorMessage			.=		'There was no valid value for either "variants.variant_type" or "variants.alternate_bases".';
	}

	return $errorMessage;

}

################################################################################

sub _createBiosampleQuery {

	my $qPar						=		$_[0];

	my $qObj						=		{};
	my $qKey;
	my @qItems;
	my @qList;

	$qKey								=		'bio_characteristics.ontology_terms.term_id';
	@qItems							=		@{ $qPar->{$qKey} };

	foreach (grep{ /.../ } @qItems) {

		push(
			@qList,
			{ $qKey => $_ },
		);

	}

	if (@qList == 1) {

		$qObj							=		$qList[0];

	} elsif (@qList > 1) {

		$qObj->{ '$or' }	=		[ @qList ];

	}

	return $qObj;

}

################################################################################

sub _createVariantQuery {

	my $qPar						=		$_[0];

	my $qObj						=		{};

	if ($qPar->{variant_type} =~ /^D(?:UP)|(?:EL)$/) {

		$qObj							=		{
			'$and' => [
				{	reference_name	=>	$qPar->{reference_name} },
				{	variant_type 		=>	$qPar->{variant_type} },
				{	start				=>	{ '$gte'	=>	1 * $qPar->{start}->[0] } },
				{	start				=>	{ '$lte'	=>	1 * $qPar->{start}->[1] } },
				{ end 				=>	{ '$gte'	=>	1 * $qPar->{end}->[0] } },
				{ end 				=>	{ '$lte'	=>	1 * $qPar->{end}->[1] } },
			],
		};

	} elsif ($qPar->{alternate_bases} =~ /^[ATGC]+?$/) {

		$qObj							=		{
			'$and' => [
				{	reference_name	=>	$qPar->{reference_name} },
				{	alternate_bases =>	$qPar->{alternate_bases} },
				{	start				=>	1 * $qPar->{start}->[0] },
			],
		};

	}

	return $qObj;

}

1;

#!/usr/bin/perl -w

use strict;
use warnings;
use POSIX;
use File::Basename;
# use Data::Dumper;

use Getopt::Long;

my $help=0;
my $verbose=0;
my $yestoall=0;
my $clear=0;
my $info=0;
my $noverify=0;

Getopt::Long::Configure(qw(gnu_getopt));
GetOptions(
           'help|h'    => \$help,
#            'verbose|v' => \$verbose,
           'y'         => \$yestoall,
           'clear|c'   => \$clear,
           'info|i'    => \$info,
           'noverify|v'  => \$noverify,
          );


          

my @pages;
my $page;

# my $header_page_addr = 0x7000;
my $header_page_addr = 0x3000; # mdc upgrade

my $trbflash = "/workdir/newtrbnettools/trbnettools/bin/trbflash";

my $FPGA            = $ARGV[0];
my $settings_file   = (defined($ARGV[1])) ? $ARGV[1] : "/dev/null";

if ($help or not(defined($FPGA)) ) {
help();
}

if ($info) {

#   my $infostring ="";
#   my $raw_page = qx"$trbflash dumppage $FPGA $header_page_addr";
#   for my $line (split("\n",$raw_page)) {
#     if ($line =~ m/^0x\S\S  (\S\S ){16}  ((\S){16})/){
#       $infostring.=$2;
#     }
#   }
  
  my $infostring = get_page($FPGA,$header_page_addr);
  
  unless ( substr($infostring,0,8) eq "SLOWCTRL" ) {
    print "found no default slow control settings in FPGA $FPGA\n";
    exit;
  }
  
  my $filename        = substr($infostring,32,32);
  my $flash_date      = substr($infostring,96,32);
  my $setfile_moddate = substr($infostring,64,32);
  my $no_pages        = unpack("l",reverse(split("",substr($infostring,12,4))));
  my $no_registers    = unpack("l",reverse(split("",substr($infostring,8,4))));
  
  $filename        =~ s/\.+$//;
  $flash_date      =~ s/\.+$//;
  $setfile_moddate =~ s/\.+$//;
  
  print "found default slow control settings in FPGA $FPGA\n";
  print "  from settings file  $filename\n";
  print "  last modified at    $setfile_moddate\n";
  print "  flashed at          $flash_date\n";
  print "  number of pages     $no_pages\n";
  print "  number of registers $no_registers\n";
  
  exit;
}


my $epoch_timestamp = (stat($settings_file))[9];
my $settings_file_mod_date = strftime("%Y-%m-%d_%H:%M:%S\n",localtime($epoch_timestamp)); # modification date
my $flash_timestamp        = strftime("%Y-%m-%d_%H:%M:%S\n",localtime());                 # now

my $registers_per_page = 42;

my $sc_data = {};






if (defined($settings_file) and not($settings_file eq "/dev/null") ) {

  # load settings from settings file
  open(FH,$settings_file) or die "could not open settings file $settings_file\n";
  my @lines = <FH>;
  close(FH);

  for my $line (@lines) {
    next unless $line =~ m/(^[xXa-fA-F0-9]+)\s+([xXa-fA-F0-9]+)/;
    $sc_data->{eval($1)} = eval($2); # convert hex/binary/decimal strings to numbers
  }

} elsif ($clear) {
  print "clearing the settings in FPGA $FPGA\n";
} else {
  help();
}

# write slow control data to pages

my $registers_to_read = 0;
my $register_counter_on_page = 0;
$page = chr(0) x 256; # initialize empty page;

my @addresses = sort { $a <=> $b } keys %{$sc_data};
for my $addr (@addresses) {
  
  insert_at(\$page,6*$register_counter_on_page,   my_uint($addr,             2) );
  insert_at(\$page,6*$register_counter_on_page+2, my_uint($sc_data->{$addr}, 4) );
  
  $registers_to_read++;
  $register_counter_on_page = ($registers_to_read)%($registers_per_page);
  
  if ( ($register_counter_on_page == 0) or ($registers_to_read == scalar(@addresses)) ) {
    push(@pages,$page);
    $page = chr(0) x 256; # initialize empty page;
  }
  
}


# compose header page
$page = chr(0) x 256; # initialize empty page;

my $pages_to_read = ceil($registers_to_read/42); 
unless($clear) {
  insert_at(\$page,0,  "SLOWCTRL" );

  insert_at(\$page,8,  my_uint($registers_to_read, 4) );
  insert_at(\$page,12, my_uint($pages_to_read,     4) );

  insert_at(\$page,32,(fileparse($settings_file))[0]); # filename only
  insert_at(\$page,64,$settings_file_mod_date); # modification date timestamp
  insert_at(\$page,96,$flash_timestamp); # flash timestamp
}
unshift(@pages,substr($page,0,256)); # push current page to the pages array, 





my $trbflash_options = "";
$trbflash_options.= " -y " if $yestoall;

  my $temp_file = qx%mktemp%;
  open(FILE,"> $temp_file") or die "could not open temporary file $temp_file for writing!\n";
  binmode(FILE);
  print FILE join("",@pages);
  close(FILE);
  system("$trbflash $trbflash_options flash_at_page $FPGA $header_page_addr $temp_file");
  system("rm $temp_file");


unless ($noverify) {
  #read header page
#   my $raw_page = qx"$trbflash dumppage $FPGA $header_page_addr";

  my $header_page = get_page($FPGA, $header_page_addr);
  my $no_pages    = unpack("l",reverse(split("",substr($header_page,12,4))));
#   print "number of pages : $no_pages\n";
  my $mismatch = 0;
  
  if ($no_pages == $pages_to_read) {
    for (my $i = 0; $i le $no_pages; $i++) {
      my $cur_page;
      if($i == 0) {
        $cur_page = $header_page;
      } else {
        $cur_page = get_page($FPGA,$header_page_addr+$i);
      }
      if ($cur_page eq $pages[$i]) {
        print "page $i/$no_pages verified\n";
      } else {
        print "page $i/$no_pages mismatch!\n";
        $mismatch++;
      }
    }
  
  
  } else {
    print "number of pages mismatch!";
    $mismatch++;
  }
  
  die "Memory verification failed! To ensure a safe FPGA behaviour, try again, or at least issue\n".
      "flash_settings.pl $FPGA --clear\nto clear the corrupted default settings\n" if $mismatch;
  
  
}

# system("xxd $temp_file");
# print "$temp_file\n";





sub get_page {
  my $FPGA = shift;
  my $page = shift;
  my $raw_page = qx"$trbflash dumppage $FPGA $page 2>&1";
  my $data;
  for my $line (split("\n",$raw_page)) {
    if ($line =~ m/^0x\S\S  ((\S\S ){16})  ((.){16})/){
      my $hex_nibbles = $1;
      $hex_nibbles =~ s/\s//g;
      $data .= pack("H*",$hex_nibbles);
      # print "$line \n LEN:";
      # print length $line;
      # print "\n";
    }
  }
  return $data if (length($data) == 256);
  die "could not read page $page from flash with $trbflash dumppage $FPGA $page";
}


sub insert_at {

  my $pageRef = shift;
  my $pos     = shift;
  my $string  = shift;
  
  substr($$pageRef,$pos,length($string)) = $string;
}

sub my_uint {
  my $number = floor(shift);
  my $bytes  = shift;
  my @out = ();
  
  for my $i (1..$bytes) {
    push(@out,chr($number & 0xFF));
    $number = floor($number/256);
  }
  
  return join("",reverse @out);
}

sub help {
print <<EOF;
usage:

  flash_settings.pl [options] <FPGA addr> [settings file]
  
options:

  --help|-h       show help message
  -y              pass "yes to all" option to trbflash
  --clear|-c      clear settings in given FPGA
  --noverify|-v   do not verify the written memory area
  --info|-i       show information summary about settings
                  in the flash
  
settings file format:

<sc addr> <value>
<sc addr> <value>
<sc addr> <value>
...

2015 by Michael Wiebusch (m.wiebusch\@gsi.de)
EOF
exit;
}

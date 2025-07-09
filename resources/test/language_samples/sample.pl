#!/usr/bin/perl

# Sample Perl program
use strict;
use warnings;
use feature 'say';
use Data::Dumper;
use List::Util qw(sum max min grep);

# Define a package for Person
package Person {
    sub new {
        my ($class, %args) = @_;
        my $self = {
            name  => $args{name} // '',
            age   => $args{age} // 0,
            email => $args{email} // '',
        };
        bless $self, $class;
        return $self;
    }
    
    sub greet {
        my $self = shift;
        return "Hello, $self->{name}! You are $self->{age} years old.";
    }
    
    sub is_adult {
        my $self = shift;
        return $self->{age} >= 18;
    }
    
    sub to_string {
        my $self = shift;
        return sprintf("Person(name='%s', age=%d, email='%s')", 
                      $self->{name}, $self->{age}, $self->{email});
    }
}

# Main package
package main;

sub main {
    say "Perl Programming Example";
    
    # Create people
    my @people = (
        Person->new(name => 'Alice', age => 30, email => 'alice@example.com'),
        Person->new(name => 'Bob', age => 17, email => 'bob@example.com'),
        Person->new(name => 'Charlie', age => 35, email => 'charlie@example.com'),
        Person->new(name => 'Diana', age => 25, email => 'diana@example.com'),
    );
    
    say "\nAll people:";
    for my $person (@people) {
        say $person->greet();
    }
    
    # Filter adults using grep
    my @adults = grep { $_->is_adult() } @people;
    say "\nAdults:";
    for my $adult (@adults) {
        say "- $adult->{name}";
    }
    
    # Array and hash operations
    array_operations();
    hash_operations();
    
    # Regular expressions
    regex_demo();
    
    # File operations
    file_operations();
    
    # References and data structures
    references_demo();
    
    # Subroutines and closures
    subroutines_demo();
    
    # String manipulation
    string_manipulation();
}

sub array_operations {
    say "\nArray Operations:";
    
    my @numbers = (1..10);
    say "Numbers: @numbers";
    
    # Map operation
    my @squares = map { $_ ** 2 } @numbers;
    say "Squares: @squares";
    
    # Grep (filter) operation
    my @even_numbers = grep { $_ % 2 == 0 } @numbers;
    say "Even numbers: @even_numbers";
    
    # Array statistics
    my $sum = sum(@numbers);
    my $max = max(@numbers);
    my $min = min(@numbers);
    my $count = @numbers;
    my $average = $sum / $count;
    
    say "Sum: $sum, Average: $average, Min: $min, Max: $max";
    
    # Array slicing
    my @slice = @numbers[2..5];
    say "Slice [2..5]: @slice";
    
    # Sort operations
    my @words = qw(banana apple cherry date elderberry);
    my @sorted_words = sort @words;
    my @sorted_by_length = sort { length($a) <=> length($b) } @words;
    
    say "Original words: @words";
    say "Sorted alphabetically: @sorted_words";
    say "Sorted by length: @sorted_by_length";
}

sub hash_operations {
    say "\nHash Operations:";
    
    # Create hash
    my %scores = (
        'Alice'   => 95,
        'Bob'     => 87,
        'Charlie' => 92,
        'Diana'   => 89,
    );
    
    say "Scores:";
    for my $name (sort keys %scores) {
        say "  $name: $scores{$name}";
    }
    
    # Hash operations
    my @names = keys %scores;
    my @values = values %scores;
    my $total_score = sum(@values);
    my $avg_score = $total_score / @names;
    
    say "Average score: $avg_score";
    
    # Hash of arrays
    my %subjects = (
        'Alice'   => ['Math', 'Science', 'English'],
        'Bob'     => ['Math', 'Art'],
        'Charlie' => ['Science', 'History', 'Math'],
    );
    
    say "\nSubjects per student:";
    for my $student (sort keys %subjects) {
        my $subjects_list = join(', ', @{$subjects{$student}});
        say "  $student: $subjects_list";
    }
}

sub regex_demo {
    say "\nRegular Expressions Demo:";
    
    my @texts = (
        'alice@example.com',
        'not-an-email',
        'bob.smith@company.org',
        'invalid@',
        'charlie@test.co.uk',
    );
    
    # Email validation regex
    my $email_regex = qr/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    
    say "Email validation:";
    for my $text (@texts) {
        if ($text =~ $email_regex) {
            say "  ✓ $text is a valid email";
        } else {
            say "  ✗ $text is not a valid email";
        }
    }
    
    # Text processing with regex
    my $text = "The quick brown fox jumps over the lazy dog.";
    say "\nOriginal text: $text";
    
    # Extract words
    my @words = $text =~ /\b\w+\b/g;
    say "Extracted words: @words";
    
    # Count vowels
    my $vowel_count = () = $text =~ /[aeiou]/gi;
    say "Vowel count: $vowel_count";
    
    # Replace words
    my $modified = $text;
    $modified =~ s/\bthe\b/THE/gi;
    say "Modified text: $modified";
}

sub file_operations {
    say "\nFile Operations Demo:";
    
    my $filename = '/tmp/perl_sample.txt';
    
    # Write to file
    open(my $fh, '>', $filename) or die "Cannot open $filename: $!";
    print $fh "Hello, World!\n";
    print $fh "This is a sample file.\n";
    print $fh "Created by Perl script.\n";
    close($fh);
    
    say "Written to $filename";
    
    # Read from file
    open($fh, '<', $filename) or die "Cannot open $filename: $!";
    my @lines = <$fh>;
    close($fh);
    
    say "File contents:";
    for my $i (0..$#lines) {
        chomp $lines[$i];
        say "  Line " . ($i + 1) . ": $lines[$i]";
    }
    
    # File information
    if (-e $filename) {
        my $size = -s $filename;
        my $mtime = (stat($filename))[9];
        say "File size: $size bytes";
        say "Last modified: " . localtime($mtime);
    }
    
    # Clean up
    unlink $filename;
    say "Cleaned up temporary file";
}

sub references_demo {
    say "\nReferences and Data Structures:";
    
    # Array reference
    my $array_ref = [1, 2, 3, 4, 5];
    say "Array reference: " . join(', ', @$array_ref);
    
    # Hash reference
    my $hash_ref = {
        name => 'Alice',
        age  => 30,
        hobbies => ['reading', 'coding', 'hiking'],
    };
    
    say "Hash reference:";
    say "  Name: $hash_ref->{name}";
    say "  Age: $hash_ref->{age}";
    say "  Hobbies: " . join(', ', @{$hash_ref->{hobbies}});
    
    # Complex data structure
    my $complex_data = {
        users => [
            { id => 1, name => 'Alice', active => 1 },
            { id => 2, name => 'Bob', active => 0 },
            { id => 3, name => 'Charlie', active => 1 },
        ],
        settings => {
            theme => 'dark',
            language => 'en',
            notifications => 1,
        },
    };
    
    say "\nComplex data structure:";
    for my $user (@{$complex_data->{users}}) {
        my $status = $user->{active} ? 'active' : 'inactive';
        say "  User $user->{id}: $user->{name} ($status)";
    }
    
    say "Settings:";
    for my $key (sort keys %{$complex_data->{settings}}) {
        say "  $key: $complex_data->{settings}{$key}";
    }
}

sub subroutines_demo {
    say "\nSubroutines and Closures:";
    
    # Simple subroutine
    sub factorial {
        my $n = shift;
        return 1 if $n <= 1;
        return $n * factorial($n - 1);
    }
    
    say "Factorial of 5: " . factorial(5);
    
    # Subroutine with multiple return values
    sub statistics {
        my @numbers = @_;
        my $sum = sum(@numbers);
        my $count = @numbers;
        my $mean = $sum / $count;
        my $min = min(@numbers);
        my $max = max(@numbers);
        
        return ($sum, $mean, $min, $max);
    }
    
    my @data = (10, 20, 30, 40, 50);
    my ($total, $average, $minimum, $maximum) = statistics(@data);
    say "Statistics for (@data):";
    say "  Total: $total, Average: $average, Min: $minimum, Max: $maximum";
    
    # Closure example
    sub make_counter {
        my $count = 0;
        return sub {
            my $increment = shift // 1;
            $count += $increment;
            return $count;
        };
    }
    
    my $counter = make_counter();
    say "Counter: " . $counter->();
    say "Counter: " . $counter->(5);
    say "Counter: " . $counter->();
}

sub string_manipulation {
    say "\nString Manipulation:";
    
    my $text = "  Hello, Perl World!  ";
    say "Original: '$text'";
    
    # String operations
    my $trimmed = $text;
    $trimmed =~ s/^\s+|\s+$//g;  # Trim whitespace
    say "Trimmed: '$trimmed'";
    
    my $uppercase = uc($trimmed);
    my $lowercase = lc($trimmed);
    say "Uppercase: $uppercase";
    say "Lowercase: $lowercase";
    
    # String splitting
    my @words = split(/\s+/, $trimmed);
    say "Words: @words";
    
    # String joining
    my $joined = join(' | ', @words);
    say "Joined: $joined";
    
    # String substitution
    my $replaced = $trimmed;
    $replaced =~ s/Perl/Amazing Perl/g;
    say "Replaced: $replaced";
    
    # String length and substring
    say "Length: " . length($trimmed);
    say "Substring (0, 5): '" . substr($trimmed, 0, 5) . "'";
    
    # Here document
    my $here_doc = <<'END_TEXT';
This is a here document.
It can span multiple lines.
Very useful for large text blocks.
END_TEXT
    
    say "Here document:";
    print $here_doc;
}

# Run main function
main() unless caller;

__END__

=head1 NAME

sample.pl - Sample Perl program demonstrating various features

=head1 DESCRIPTION

This script demonstrates various Perl programming concepts including:
- Object-oriented programming
- Array and hash operations
- Regular expressions
- File I/O
- References and complex data structures
- Subroutines and closures
- String manipulation

=head1 AUTHOR

Sample Author

=cut 
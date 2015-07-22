#!/usr/bin/env python
import os, sys
import csv, codecs, cStringIO
from simple_salesforce import Salesforce

######################################
##
## Dumps Salesforce data to CSV.
##
## 1. To authenticate to SF, create a plain text file called .sfauth
## (not .sfauth.txt, nor sfauth.txt, nor sfauth.docx) that has your
## username, password, and security token.  Restrict permissions on
## .sfauth by running "chmod 600 .sfauth" or similar.
##
## 2. The SOQL query we will run is defined here.  It could be any
## SOQL query, but I'm just getting a comma separated list of columns
## and a table name from the first two command line arguments, and
## there's no where clause so it pulls down all the values (and not
## just the first fifty or the first two thousand or whatever).
##
## 3. The actual work is done down here.  I've segregated into this
## section all the code that probably shouldn't need to be changed
## (except to fix bugs, in which case a pull request would be great).
##.
######################################


######################################
##
## 1. Auth stuff
##
with open(".sfauth") as f:
    for line in f:
        k,v = line.split('=')
        os.environ[k] = v.strip()
username = os.environ['SFUSERNAME'] # IF YOU SEE AUTH CREDENTIALS CHECKED IN HERE THAT'S A BUG
password = os.environ['SFPASSWORD'] # IF YOU SEE AUTH CREDENTIALS CHECKED IN HERE THAT'S A BUG
security_token = os.environ['SFSECURITYTOKEN'] # IF YOU SEE AUTH CREDENTIALS CHECKED IN HERE THAT'S A BUG

######################################
##
## 2. Query stuff
##

comma_separated_column_names = sys.argv[1]
table = sys.argv[2]

soql = u"SELECT %s FROM %s" ## <-- this is the SOQL we will run.  any valid SOQL should be fine.


######################################
##
## 3. The implementation: Write csv to stdout
##

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()
        self.skipped_rows = 0

    def writerow(self, row):
        try:
            self.writer.writerow([s and s.encode("utf-8") or '' for s in row])
        except AttributeError:
            print
            self.skipped_rows = self.skipped_rows + 1
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

def dig_out_value(c, r, t):
    dotIdx = c.find('.')
    c1 = c[:dotIdx]
    c2 = c[1+dotIdx:]
    if dotIdx > 0 and not c1 == table:
        res = r[c1][c2]
    else:
        res = r[c2]
    if type(res) == str:
        return res.replace('\n', '\\n').replace('\r', '\\r').strip()
    else:
        return res


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

columns = [s.strip() for s in comma_separated_column_names.split(",")]
writer = UnicodeWriter(sys.stdout, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
writer.writerow(columns)
printed_lines = 0
skipped_lines = 0
line_number = 0
with open("failures.log", "w") as fail_log:

    sf = Salesforce(username=username, password=password, security_token=security_token, sandbox=False)

    result = sf.query(soql % (comma_separated_column_names, table))
    done = False
    while not done:
        for r in result["records"]:
            line_number = line_number + 1
            # Here's where we actually print...
            try:
                row = [dig_out_value(c, r, table) for c in columns]
                writer.writerow(row)
                printed_lines = printed_lines + 1
            except TypeError:
                fail_log.write("# %d\n" % line_number)
                fail_log.write(str(r))
                fail_log.write("\n")
                skipped_lines = skipped_lines + 1
        if result['done']:
            done = True
        else:
            result = sf.query_more(result['nextRecordsUrl'], identifier_is_url=True)

if skipped_lines > 0:
    sys.stderr.write("WARNING: Skipped %d lines.\n" % skipped_lines)
    sys.exit(0)
else:
    sys.stderr.write("OK: wrote all lines successfully.\n")
    sys.exit(0)

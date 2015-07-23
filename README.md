# soqldump
A simple script to dump Salesforce data to CSV.

# Install/config

You will need Python 2.7 and the `simple_salesforce` library
installed.  Then you'll need to put your Salesforce credentials either
in a file called `.sfauth` (the approach I recommend) or in
environment variables.

## Installing prerequisites

If you are on a Mac or Linux machine you already have python
installed.  (You want Python 2.7.x, not Python 3.x.)  If you are on
Windows you'll probably need to download from http://python.org and
install as appropriate.  You need to be able to successfully say
`python` and `pip` from a command prompt.  (The tutorial installation
instructions at
[https://docs.python.org/2/tutorial/interpreter.html](https://docs.python.org/2/tutorial/interpreter.html)
show you how to add `python` to `path` environment variable; if
`python` was in `C:\python27` then `pip` will be in
`C:\python27\scripts`.)

Once `pip` runs, install the `simple_salesforce` library:

```bash
pip install simple_salesforce
```

When everything is installed properly you should be able to run the
following at a command prompt:

```bash
$ python
Python 2.7.10 (default, Jun 10 2015, 19:42:47)
[GCC 4.2.1 Compatible Apple LLVM 6.1.0 (clang-602.0.53)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import simple_salesforce
>>>
```

If that last bit didn't throw any errors, then you have all the
requisite software installed.

Now you need to configure the Salesforce credentials that
`soqldump.py` will use.  Edit the plain text file called `.sfauth`
(and don't save it as `.sfauth.txt`, nor `sfauth.txt`, nor god forbid
`sfauth.docx`) with your username, password, and security token.

Restrict permissions on `.sfauth` by running `chmod 600 .sfauth` on
Mac/Linux or whatever similar thing one should do on Windows to
sensitive files.

# Use

```bash
python soqldump.py "Id,FirstName,PhoneNumber" Account > name_and_number.csv
```

The comma separated list of column names (the "API names", not the
human friendly names) should be surrounded by double quotes.  (No
whitespace between the commas.)  The table (object) name probably
doesn't need double quotes.

On all three platforms, the `>` means "redirect output to a file of
the following name", which in this example is `name_and_number.csv`.
I strongly recommend that you embed the current date and time in the
filename.  For example:

```bash
TS=`date +%Y_%m_%d_%H%M` python soqldump.py "Id,Name,ShoeSize"  "Shoe" > ${TS}_shoesize_and_name.csv
```

Also, I have occasionally seen this program write blank lines in its output.  If on Mac/Linux, remove those by piping the output through `sed`:

```bash
TS=`date +%Y_%m_%d_%H%M` python soqldump.py "Id,Name,ShoeSize"  "Shoe" | sed '/^\s*$/d' > ${TS}_shoesize_and_name.csv
```

# FAQ

**Q:** Can't I just write "select * from SomeTable" in SOQL?

**A:** Astonishingly, no!

**Q:** What if I want to get a list of columns?

**A:** Use
[https://github.com/heroku/force](https://github.com/heroku/force).
The `force` binary is actually an excellent piece of software, but I
wrote `soqldump` because for some reason `force` doesn't have a
version of `force query` that doesn't append `where rownum < 2001` to
the end of your query.  It's maddening.

**Q:** How about running arbitrary SOQL?

**A:** Edit the `soql` variable in "section 2" of `soqldump.py`.

# License

MIT --- See LICENSE.

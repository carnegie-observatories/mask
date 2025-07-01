## Backend
### tests
cd into backend/mask/ and run `pytest`

For vscode activate venv then do which python to get interpreter path

To send a post request with a file through postman, go to Body -> form-data -> add a key named "file" and switch the type to file.
Then upload your file. Next, go to headers and add a new header named "Content-Disposition" with the value
`form-data; name="file"; filename="your_file_name_here"`

TODO
- add another test case for .obj files in object upload
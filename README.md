## Backend
### tests
cd into backend/mask/ and run `pytest`

For vscode activate venv then do which python to get interpreter path

To send a post request with a file through postman, go to Body -> form-data -> add a key named "file" and switch the type to file.
Then upload your file. Next, go to headers and add a new header named "Content-Disposition" with the value
`form-data; name="file"; filename="your_file_name_here"`

TODO
- convert .obj ra from hrs to degs
- endpoint get list of available grisms and filters
- convert instrument config to json
- 
-
- endpoint to download json formatting

Daily
- Tests for instrument config
- format slits into a json file
- endpoint to retrieve slits


## Backend
### tests
cd into backend/mask/ and run `pytest`

For vscode activate venv then do which python to get interpreter path

To send a post request with a file through postman, go to Body -> form-data -> add a key named "file" and switch the type to file.
Then upload your file. Next, go to headers and add a new header named "Content-Disposition" with the value
`form-data; name="file"; filename="your_file_name_here"`

# API Endpoints
## Object API (/api/objects/)
### POST `/api/objects/upload/`
- Upload a file (.obj or JSON) to create a new object list for a user.
- Request data: file, user_id, list_name
- Returns IDs of created objects and the list name.

### GET `/api/objects/viewlist/?list_name=<name>`
- Retrieve the object lists and the objects it contains.

## Mask API (/api/masks/)
### GET `/api/masks/{name}/`
- Retrieve mask details by mask name. Includes status, instrument version, setup, object lists, excluded objects, and features.

### POST `/api/masks/generate/`
- Generate a mask from provided data.
- Request JSON body should include filename, objects (either a list of object IDs or an object list name), and instrument setup.
- Returns path to the generated .SMF file if successful.

## Instrument API (/api/instruments/)
### GET `/api/instruments/{instrument_name}?version=<version>`
Retrieve instrument configuration by instrument name.
Optional query param version returns a specific version; otherwise returns latest.

### POST `/api/instruments/uploadconfig/`
Upload a new instrument configuration.
Stores instrument, filters, dispersers, and auxillary info
Automatically inputs version if existing configs found.

TODO
- convert .obj ra from hrs to degs
- endpoint get list of available grisms and filters
- convert instrument config to json
- endpoint to download json formatting

Daily
- Tests for instrument config
- format slits into a json file
- endpoint to retrieve slits


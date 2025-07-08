# Backend

## Running locally
1. run `uv venv` and `source .venv/bin/activate`
2. cd into `backend` folder
3. run `python manage.py runserver`
Then, the API should be up and running. I like to use Postman to interact with the API though any method should work. Note that anytime you're uploading a file, you should upload it using form-data with the key, "file".
To send a POST request with a file through Postman, go to Body -> form-data -> add a key named "file" and switch the type to file.
Then upload your file. Next, go to headers and add a new header named "Content-Disposition" with the value `form-data; name="file"; filename="your_file_name_here"`

To get less warnings in vscode using the venv, do `which python` to get interpreter path.

### tests
run `pytest`

## API Endpoints
### Object API (/api/objects/)
#### POST `/api/objects/upload/`
- Upload a file (.obj or JSON) to create a new object list for a user.
- Request data: file, user_id, list_name
- Returns IDs of created objects and the list name.

#### GET `/api/objects/viewlist/?list_name=<name>`
- Retrieve the object lists and the objects it contains.

## Mask API (/api/masks/)
#### GET `/api/masks/{name}/`
- Retrieve mask details by mask name. Includes status, instrument version, setup, object lists, excluded objects, and features.

#### POST `/api/masks/generate/`
- Generate a mask from provided data.
- Request JSON body should include filename, objects (either a list of object IDs or an object list name), and instrument setup.
- Returns path to the generated .SMF file if successful.

## Instrument API (/api/instruments/)
#### GET `/api/instruments/{instrument_name}?version=<version>`
- Retrieve instrument configuration by instrument name.
- Optional query param version returns a specific version; otherwise returns latest.

#### POST `/api/instruments/uploadconfig/`
- Upload a new instrument configuration.
- Stores instrument, filters, dispersers, and auxillary info
- Automatically inputs version if existing configs found.

TODO
- convert .obj ra from hrs to degs

Daily
- Tests for instrument config
- Tests for instrument config

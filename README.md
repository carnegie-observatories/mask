# Backend

## Running locally
1. install uv using these instructions [here](https://docs.astral.sh/uv/).
2. In the `\mask` folder, run `uv venv`, `uv sync`, and `source .venv/bin/activate`
3. cd into `backend` folder
4. run `python manage.py migrate` and `python manage.py runserver`

Then, the API should be up and running. I like to use Postman to interact with the API though any method should work. Note that anytime you're uploading a file, you should upload it using form-data with the key, "file".
To send a POST request with a file through Postman, go to Body -> form-data -> add a key named "file" and switch the type to file.
Then upload your file. Next, go to headers and add a new header named "Content-Disposition" with the value `form-data; name="file"; filename="your_file_name_here"`

To get less warnings in vscode using the venv, do `which python` to get interpreter path.
## Suggested workflow
1. Upload instrument config
2. Create Project
3. Upload Image
4. Upload Objects
5. Generate Mask

### tests
run `pytest`

## API Endpoints
Almost all endpoints require a `user-id` header
### Project API (/api/project/)
#### POST `/api/project/create/`
- Projects group images, masks, and an (optional) associated object list. 
- Body: project_name (string), center_ra (string/number), center_dec (string/number)
#### GET `/api/project/{project_name}/`
- Retrieve high‑level project info: listed image names and mask names.

### Object API (/api/objects/)
#### POST `/api/objects/<project>/upload/`
- Upload a file (.obj or JSON) to create a new object list for a user.
- Request data: file, user_id, list_name
- Returns IDs of created objects and the list name.

#### GET `/api/objects/viewlist/?list_name=<name>`
- Retrieve the object lists and the objects it contains.

### Mask API (/api/masks/)
#### GET `/api/masks/{name}/`
- Retrieve mask details by mask name. Includes status, instrument version, setup, object lists, excluded objects, and features.

#### POST `/api/masks/generate/`
- Generate a mask from provided data.
- Request JSON body should include filename, objects (either a list of object IDs or an object list name), and instrument setup.
- Returns path to the generated .SMF file if successful.

#### POST `/api/masks/complete/`
- Mark a mask as COMPLETED (required before machine code generation).

#### DELETE `/api/masks/delete/?project_name=<proj>&mask_name=<mask>`

### Machine API (/api/machine)
#### POST `/api/machine/generate/`
- Generate the machine code, mask must be marked as COMPLETED
- Form Data: project_name (string), mask_name (string)
#### GET `/api/machine/get-machine-code/?project_name=<proj>&mask_name=<mask>`
- Get the generated machine code


### Instrument API (/api/instruments/)
#### GET `/api/instruments/{instrument_name}?version=<version>`
- Retrieve instrument configuration by instrument name.
- Optional query param version returns a specific version; otherwise returns latest.

#### POST `/api/instruments/uploadconfig/`
- Upload a new instrument configuration.
- Stores instrument, filters, dispersers, and auxillary info
- Automatically inputs version if existing configs found.

### Image API (/api/images/)
#### GET `/api/images/getimg/?project_name=<proj>&img_name=<file>`
- Return the image file (content type image/jpeg).
#### POST `/api/images/uploadimg/`
- Form fields: project_name (string), image (file upload)







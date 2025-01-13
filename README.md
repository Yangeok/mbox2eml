# mbox2eml: Convert Mbox to EML Files Easily

`mbox2eml` is a Python utility for converting `.mbox` files (used by many email clients to store messages) into individual `.eml` files. This tool is perfect for anyone needing to export or process emails from `.mbox` archives.

## Features

- Converts `.mbox` files into multiple `.eml` files.
- Automatically creates the output directory if it doesn't exist.
- Handles single-part and multi-part email messages.
- Validates `.mbox` file format before conversion.
- Provides detailed error handling for corrupted or inaccessible files.
- Supports Unicode and special characters in email headers and content.

## Installation

```sh
pip install mbox2eml
```

## Usage

The utility provides a command-line interface (CLI) for easy usage.

### Command-line Arguments

- `--file, -f`: Path to the input `.mbox` file (required).
- `--output_dir, -o`: Path to the output directory where `.eml` files will be saved (required).

### Example

Convert an `.mbox` file to `.eml` files:

```sh
mbox2eml --file path/to/input.mbox --output_dir path/to/output/
```

After running the command, all emails in the `.mbox` file will be converted to `.eml` files in the specified output directory.

## Code Example (Programmatic Use)

You can also use the utility programmatically in Python:

```py
from mbox2eml import convert_mbox_to_eml

mbox_file = "path/to/input.mbox"
output_dir = "path/to/output"

success, fail = convert_mbox_to_eml(mbox_file, output_dir)
print(f"Conversion completed: {success} succeeded, {fail} failed")
```

## Error Handling

The tool gracefully handles various edge cases:

- **File Not Found**: Raises `FileNotFoundError` if the `.mbox` file doesn't exist.
- **Permission Issues**: Raises `PermissionError` if the `.mbox` file or output directory is not accessible.
- **Invalid Output Path**: Raises `IsADirectoryError` if the output directory path is a file.
- **Empty Mbox**: Outputs a message if the `.mbox` file is empty but does not treat it as an error.
- **Corrupted Mbox**: Skips invalid messages while continuing to process others.

## Development

Clone the repository to contribute or run the utility locally:

```sh
git clone https://github.com/yangeok/mbox2eml.git
cd mbox2eml
```

Install dependencies and run the script:

```sh
python -m pip install -r requirements.txt
python mbox2eml.py --file path/to/input.mbox --output_dir path/to/output/
```

## Tests

The package includes a comprehensive test suite to ensure stability and handle edge cases.

Run the test suite with `pytest`:

Run the tests in watch mode:

```sh
poetry run test-watch
```

Run the tests normally:

```sh
poetry run test
```

Run tests in debug mode:

```sh
poetry run test-debug
```

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to report bugs or request features.

## Author

Developed by **Yangwook Ian Jeong**. For inquiries, please contact `yangwoookee@gmail.com`.

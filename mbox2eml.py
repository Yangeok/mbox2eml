import argparse
import mailbox
import os
from pathlib import Path
from typing import BinaryIO, Tuple, Union

from tqdm import tqdm


def convert_mbox_to_eml(
    mbox_file: Union[str, Path], output_dir: Union[str, Path]
) -> Tuple[int, int]:
    """Convert an mbox file into multiple .eml files.

    Args:
        mbox_file (Union[str, Path]): Path to the source mbox file
        output_dir (Union[str, Path]): Directory where .eml files will be saved

    Returns:
        Tuple[int, int]: A tuple containing (number of successful conversions, number of failed conversions)

    Raises:
        FileNotFoundError: If the mbox file does not exist
        PermissionError: If there are permission issues with input or output files
        IsADirectoryError: If output_dir exists and is a file
    """
    mbox_path: Path = Path(mbox_file)
    output_path: Path = Path(output_dir)

    if not mbox_path.exists():
        raise FileNotFoundError(f"Mbox file not found: {mbox_path}")

    # Check if output path exists and is a file
    if output_path.exists() and output_path.is_file():
        raise IsADirectoryError(f"Output path exists and is a file: {output_path}")

    # Check input file permissions
    if not os.access(mbox_path, os.R_OK):
        raise PermissionError(f"No read permission for mbox file: {mbox_path}")

    # Check/create output directory
    if output_path.exists() and not os.access(output_path, os.W_OK):
        raise PermissionError(
            f"No write permission for output directory: {output_path}"
        )

    output_path.mkdir(parents=True, exist_ok=True)

    try:
        with open(mbox_path, "rb") as f:
            content: bytes = f.read()
            if not content:  # Check if file is empty
                print("Info: Empty mbox file")
                return 0, 0  # Empty file is not an error

            # Check if content is valid mbox format (should start with "From " line)
            if not content.startswith(b"From ") and b"\x00" in content[:10]:
                print("Error: Invalid or corrupted mbox file format")
                return 0, 1

            try:
                mbox: mailbox.mbox = mailbox.mbox(str(mbox_path))
                messages: list[mailbox.mboxMessage] = list(mbox)

                if not messages:  # No valid messages found
                    print("Info: No valid messages in mbox file")
                    return 0, 0  # No messages is not an error

                success_count: int = 0
                fail_count: int = 0
                for i, message in tqdm(enumerate(messages, 1), total=len(messages)):
                    try:
                        eml_path = output_path / f"{i}.eml"
                        if not os.access(output_path, os.W_OK):
                            raise PermissionError(
                                f"No write permission for: {eml_path}"
                            )

                        _write_eml_file(message, eml_path)
                        success_count += 1
                    except Exception as e:
                        print(f"Error processing message {i}: {str(e)}")
                        fail_count += 1

                return success_count, fail_count

            except Exception as e:
                print(f"Error parsing mbox file: {str(e)}")
                return 0, 1

    except PermissionError as e:
        raise  # Re-raise permission errors
    except Exception as e:
        print(f"Error reading mbox file: {str(e)}")
        return 0, 1


def _write_eml_file(message: mailbox.mboxMessage, eml_path: Path) -> None:
    """Write a mailbox message to an .eml file.

    Args:
        message (mailbox.mboxMessage): The email message to convert
        eml_path (Path): Path where the .eml file will be written

    Raises:
        IOError: If there are issues writing the file
    """
    with open(eml_path, "wb") as eml_file:
        # Write headers
        for header, value in message.items():
            header_line: bytes = f"{header}: {value}\n".encode(
                "utf-8", errors="replace"
            )
            eml_file.write(header_line)

        eml_file.write(b"\n")  # Separator between headers and body

        # Write body
        if not message.is_multipart():
            _write_single_part(message, eml_file)
        else:
            _write_multipart(message, eml_file)


def _write_single_part(message: mailbox.mboxMessage, eml_file: BinaryIO) -> None:
    """Write a single-part message body to the eml file.

    Args:
        message (mailbox.mboxMessage): The email message to process
        eml_file: The file object to write to

    Raises:
        IOError: If there are issues writing to the file
    """
    payload: Union[str, bytes] = message.get_payload()
    if isinstance(payload, str):
        eml_file.write(payload.encode("utf-8", errors="replace"))
    elif isinstance(payload, bytes):
        eml_file.write(payload)


def _write_multipart(message: mailbox.mboxMessage, eml_file: BinaryIO) -> None:
    """Write a multipart message body to the eml file.

    Args:
        message (mailbox.mboxMessage): The multipart email message to process
        eml_file: The file object to write to

    Raises:
        ValueError: If the multipart message has no boundary
        IOError: If there are issues writing to the file
    """
    boundary: str = message.get_boundary()
    if not boundary:
        raise ValueError("Multipart message has no boundary")

    boundary_bytes: bytes = boundary.encode("utf-8", errors="replace")
    for part in message.get_payload():
        eml_file.write(b"--" + boundary_bytes + b"\n")
        if hasattr(part, "as_bytes"):
            eml_file.write(part.as_bytes())
        else:
            part_str: str = str(part)
            eml_file.write(part_str.encode("utf-8", errors="replace"))
    eml_file.write(b"--" + boundary_bytes + b"--\n")


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Convert mbox to eml"
    )
    parser.add_argument(
        "--file",
        "-f",
        type=str,
        required=True,
        help="Path to the input mbox file, eg. 1.mbox",
    )
    parser.add_argument(
        "--output_dir",
        "-o",
        type=str,
        required=True,
        help="Path to the output directory, eg. output",
    )

    args: argparse.Namespace = parser.parse_args()

    success, fail = convert_mbox_to_eml(args.file, args.output_dir)
    print(f"\nConversion completed: {success} succeeded, {fail} failed")


if __name__ == "__main__":
    main()

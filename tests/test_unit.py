import mailbox
from email.message import EmailMessage
from pathlib import Path

import pytest

from mbox2eml import convert_mbox_to_eml


def create_test_email(subject: str, body: str) -> EmailMessage:
    """Create a test email message."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content(body)
    return msg


@pytest.fixture
def sample_mbox(tmp_path) -> Path:
    """Create a sample mbox file with multiple emails."""
    mbox_path = tmp_path / "test.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    # Add two test emails
    msg1 = create_test_email("Test Email 1", "This is test email 1")
    msg2 = create_test_email("Test Email 2", "This is test email 2")

    mbox.add(msg1)
    mbox.add(msg2)
    mbox.flush()

    return mbox_path


@pytest.fixture
def sample_mbox_single_email(tmp_path) -> Path:
    """Create a sample mbox file with a single email."""
    mbox_path = tmp_path / "single.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    msg = create_test_email("Single Test Email", "This is a single test email")
    mbox.add(msg)
    mbox.flush()

    return mbox_path


@pytest.fixture
def corrupted_mbox(tmp_path) -> Path:
    """Create a corrupted mbox file."""
    mbox_path = tmp_path / "corrupted.mbox"

    # Write invalid mbox content
    with open(mbox_path, "w") as f:
        f.write("This is not a valid mbox file format")

    return mbox_path


def test_when_mbox_file_not_found_then_raises_error():
    # Given
    nonexistent_file = "nonexistent.mbox"
    output_dir = "output"

    # When / Then
    with pytest.raises(FileNotFoundError):
        convert_mbox_to_eml(nonexistent_file, output_dir)


def test_when_converting_valid_mbox_then_creates_output_directory(
    tmp_path, sample_mbox
):
    # Given
    output_dir = tmp_path / "output"
    assert not output_dir.exists()

    # When
    convert_mbox_to_eml(sample_mbox, output_dir)

    # Then
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_when_converting_single_email_then_creates_eml_file(
    tmp_path, sample_mbox_single_email
):
    # Given
    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(sample_mbox_single_email, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


def test_when_processing_corrupted_email_then_counts_as_failure(
    tmp_path, corrupted_mbox
):
    # Given
    output_dir = tmp_path / "output"
    with open(corrupted_mbox, "wb") as f:
        # Write invalid binary data to ensure mailbox parsing fails
        f.write(b"\x00\xFF\xFF\xFF")  # Invalid mbox format

    # When
    success, fail = convert_mbox_to_eml(corrupted_mbox, output_dir)

    # Then
    assert success == 0
    assert fail == 1


def test_when_mbox_is_empty_then_no_emails_are_converted(tmp_path):
    # Given
    mbox_path = tmp_path / "empty.mbox"
    mbox = mailbox.mbox(str(mbox_path))
    mbox.flush()  # Empty mbox
    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 0
    assert fail == 0


def test_when_output_directory_exists_then_eml_files_are_added(tmp_path, sample_mbox):
    # Given
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    # Create a dummy file in the output directory
    dummy_file = output_dir / "dummy.txt"
    dummy_file.touch()

    # When
    convert_mbox_to_eml(sample_mbox, output_dir)

    # Then
    assert dummy_file.exists()  # Ensure existing files are not removed
    assert (output_dir / "1.eml").exists()
    assert (output_dir / "2.eml").exists()


def test_when_email_has_no_headers_then_eml_is_created(tmp_path):
    # Given
    mbox_path = tmp_path / "no_headers.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    # Create a message without headers
    msg = mailbox.mboxMessage()
    msg.set_payload("Body without headers")
    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


def test_when_email_is_multipart_then_eml_is_created_correctly(tmp_path):
    # Given
    mbox_path = tmp_path / "multipart.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    msg = EmailMessage()
    msg["Subject"] = "Multipart Email"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content("Plain text part")
    msg.add_alternative("<html><body>HTML part</body></html>", subtype="html")
    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()
    # Optionally, parse the .eml file and validate its structure


def test_when_output_directory_not_writable_then_raises_permission_error(
    tmp_path, sample_mbox
):
    # Given
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    output_dir.chmod(0o444)  # Read-only permissions

    # When / Then
    with pytest.raises(PermissionError):
        convert_mbox_to_eml(sample_mbox, output_dir)


def test_when_mbox_file_not_readable_then_raises_permission_error(
    tmp_path, sample_mbox
):
    # Given
    sample_mbox.chmod(0o000)  # No permissions

    output_dir = tmp_path / "output"

    # When / Then
    with pytest.raises(PermissionError):
        convert_mbox_to_eml(sample_mbox, output_dir)


def test_when_email_contains_unicode_characters_then_eml_is_created(tmp_path):
    # Given
    mbox_path = tmp_path / "unicode.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    msg = create_test_email(
        "테스트 이메일", "본문에 유니코드 문자가 포함됩니다: こんにちは"
    )
    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


def test_when_email_has_invalid_encoding_then_handles_gracefully(tmp_path):
    # Given
    mbox_path = tmp_path / "invalid_encoding.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    msg = create_test_email("Invalid Encoding", "Invalid \x80\x81 characters")
    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


def test_when_output_path_is_a_file_then_raises_error(tmp_path, sample_mbox):
    # Given
    output_dir = tmp_path / "output"
    output_dir.touch()  # Create a file instead of a directory

    # When / Then
    with pytest.raises(IsADirectoryError):
        convert_mbox_to_eml(sample_mbox, output_dir)


def test_when_email_is_nested_multipart_then_eml_is_created_correctly(tmp_path):
    # Given
    mbox_path = tmp_path / "nested_multipart.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    # Create a nested multipart email
    msg = EmailMessage()
    msg["Subject"] = "Nested Multipart Email"
    msg["From"] = "sender@example.com"
    msg["To"] = "recipient@example.com"
    msg.set_content("Outer plain text part")

    # Add an inner multipart
    inner_msg = EmailMessage()
    inner_msg.add_alternative(
        "<html><body>Inner HTML part</body></html>", subtype="html"
    )
    msg.add_attachment(
        inner_msg.as_bytes(), maintype="multipart", subtype="alternative"
    )

    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


def test_when_email_headers_contain_special_characters_then_eml_is_created(tmp_path):
    # Given
    mbox_path = tmp_path / "special_headers.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    msg = EmailMessage()
    msg["Subject"] = "테스트 🧪"
    msg["From"] = "보낸사람@example.com"
    msg["To"] = "받는사람@example.com"
    msg.set_content("본문 내용")
    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


def test_when_email_has_duplicate_headers_then_eml_is_created_correctly(tmp_path):
    # Given
    mbox_path = tmp_path / "duplicate_headers.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    msg = EmailMessage()
    msg["Received"] = "by server1.example.com"
    msg["Received"] = "by server2.example.com"
    msg["Subject"] = "Duplicate Headers Test"
    msg.set_content("Testing duplicate headers")
    mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1
    assert fail == 0
    assert (output_dir / "1.eml").exists()


@pytest.mark.slow  # Optional marker for slow tests
def test_when_mbox_file_is_large_then_all_emails_are_converted(tmp_path):
    # Given
    mbox_path = tmp_path / "large.mbox"
    mbox = mailbox.mbox(str(mbox_path))

    # Add a large number of messages
    for i in range(1000):  # Simulating 1000 messages
        msg = create_test_email(f"Subject {i}", f"Body of email {i}")
        mbox.add(msg)
    mbox.flush()

    output_dir = tmp_path / "output"

    # When
    success, fail = convert_mbox_to_eml(mbox_path, output_dir)

    # Then
    assert success == 1000
    assert fail == 0


def test_when_eml_file_already_exists_then_overwrites(tmp_path, sample_mbox):
    # Given
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "1.eml").touch()  # Pre-create file

    # When
    success, fail = convert_mbox_to_eml(sample_mbox, output_dir)

    # Then
    assert success == 2  # Both messages converted
    assert fail == 0
    assert (output_dir / "1.eml").exists()
    assert (output_dir / "2.eml").exists()

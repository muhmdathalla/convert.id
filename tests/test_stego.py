import tempfile
from pathlib import Path
from PIL import Image
from convert_id.utils.stego import hide_payload_in_image, extract_payload_from_image

def test_steganography():
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # Carrier image
        carrier = tdp / "carrier.png"
        img = Image.new("RGBA", (300, 300), color=(100, 150, 200, 255))
        img.save(carrier, format="PNG")

        # Secret payload
        secret_data = b"TOP_SECRET_ANTIGRAVITY_CONVERT_ID_2026"
        stego_out = tdp / "stego_output.png"
        
        # Test 1: Plain Steganography
        hide_payload_in_image(carrier, stego_out, secret_data, filename="secret.txt")
        assert stego_out.exists()

        extracted = extract_payload_from_image(stego_out)
        assert extracted["data"] == secret_data
        assert extracted["filename"] == "secret.txt"

        # Test 2: Encrypted Steganography with Password
        stego_enc = tdp / "stego_encrypted.png"
        hide_payload_in_image(carrier, stego_enc, secret_data, filename="secret_enc.txt", password="SuperPassword99!")
        
        extracted_enc = extract_payload_from_image(stego_enc, password="SuperPassword99!")
        assert extracted_enc["data"] == secret_data
        assert extracted_enc["filename"] == "secret_enc.txt"
        assert extracted_enc["is_encrypted"] is True

        print("Steganography test passed successfully!")

if __name__ == "__main__":
    test_steganography()

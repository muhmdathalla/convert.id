import os
import struct
import hashlib
from pathlib import Path
from PIL import Image

def _derive_key(password: str, length: int) -> bytes:
    """Simple keystream generator from password."""
    key = b""
    counter = 0
    while len(key) < length:
        h = hashlib.sha256(password.encode('utf-8') + counter.to_bytes(4, 'big')).digest()
        key += h
        counter += 1
    return key[:length]

def hide_payload_in_image(image_path: Path, output_path: Path, payload_data: bytes, filename: str = "", password: str = "") -> bool:
    """
    Hides arbitrary bytes/file into image RGB LSBs.
    Header format: [4 bytes MAGIC "STG1"][4 bytes filename_len][filename][8 bytes payload_len][payload]
    """
    img = Image.open(image_path).convert("RGBA")
    width, height = img.size
    pixels = list(img.getdata())
    
    # Max bits capacity = total pixels * 3 (R, G, B channels LSB)
    max_bits = width * height * 3
    
    magic = b"STG1"
    fn_bytes = filename.encode('utf-8')
    fn_len = len(fn_bytes)
    
    raw_header = magic + struct.pack(">I", fn_len) + fn_bytes + struct.pack(">Q", len(payload_data))
    raw_content = raw_header + payload_data
    
    if password:
        keystream = _derive_key(password, len(raw_content))
        processed_data = bytes([b ^ k for b, k in zip(raw_content, keystream)])
        # Mark with encrypted magic
        full_data = b"STGE" + processed_data
    else:
        full_data = raw_content

    total_bits = len(full_data) * 8
    if total_bits > max_bits:
        raise ValueError(f"Payload too large! Need {total_bits} bits, image only holds {max_bits} bits.")

    # Convert full_data to bit list
    bit_array = []
    for byte in full_data:
        for bit_idx in range(7, -1, -1):
            bit_array.append((byte >> bit_idx) & 1)

    new_pixels = []
    bit_cursor = 0
    total_len = len(bit_array)

    for r, g, b, a in pixels:
        channels = [r, g, b]
        for c in range(3):
            if bit_cursor < total_len:
                channels[c] = (channels[c] & ~1) | bit_array[bit_cursor]
                bit_cursor += 1
        new_pixels.append((channels[0], channels[1], channels[2], a))

    out_img = Image.new("RGBA", (width, height))
    out_img.putdata(new_pixels)
    # Output must be lossless (PNG)
    out_img.save(output_path, format="PNG")
    return True

def extract_payload_from_image(image_path: Path, password: str = "") -> dict:
    """
    Extracts hidden payload from image RGB LSBs.
    Returns dict: {"filename": str, "data": bytes, "is_encrypted": bool}
    """
    img = Image.open(image_path).convert("RGBA")
    pixels = list(img.getdata())

    # Read bits
    bits = []
    # Read first 32 bits (4 bytes) to check magic
    for r, g, b, _ in pixels:
        for c in (r, g, b):
            bits.append(c & 1)
            if len(bits) == 32:
                break
        if len(bits) == 32:
            break

    def bits_to_bytes(b_list):
        out = bytearray()
        for i in range(0, len(b_list), 8):
            byte = 0
            for b in b_list[i:i+8]:
                byte = (byte << 1) | b
            out.append(byte)
        return bytes(out)

    magic = bits_to_bytes(bits[:32])
    is_encrypted = (magic == b"STGE")

    if not is_encrypted and magic != b"STG1":
        raise ValueError("No hidden convert.id steganography payload found in this image.")

    # Extract all bits progressively
    all_bits = []
    for r, g, b, _ in pixels:
        all_bits.append(r & 1)
        all_bits.append(g & 1)
        all_bits.append(b & 1)

    all_raw_bytes = bits_to_bytes(all_bits)

    if is_encrypted:
        if not password:
            raise ValueError("This payload is encrypted with a password! Please provide --password.")
        cipher_content = all_raw_bytes[4:]
        # Decrypt first 32 bytes to read header
        temp_key = _derive_key(password, 32)
        dec_header = bytes([c ^ k for c, k in zip(cipher_content[:32], temp_key)])
        if not dec_header.startswith(b"STG1"):
            raise ValueError("Incorrect password or corrupted steganography payload.")
        
        # Read header info
        fn_len = struct.unpack(">I", dec_header[4:8])[0]
        header_size = 8 + fn_len + 8
        
        # Decrypt full needed stream
        temp_key = _derive_key(password, header_size)
        full_dec_header = bytes([c ^ k for c, k in zip(cipher_content[:header_size], temp_key)])
        fn = full_dec_header[8:8+fn_len].decode('utf-8', errors='ignore')
        payload_len = struct.unpack(">Q", full_dec_header[8+fn_len:8+fn_len+8])[0]
        
        total_needed = header_size + payload_len
        full_key = _derive_key(password, total_needed)
        full_decrypted = bytes([c ^ k for c, k in zip(cipher_content[:total_needed], full_key)])
        payload = full_decrypted[header_size:total_needed]
        return {"filename": fn, "data": payload, "is_encrypted": True}
    else:
        # Plain STG1
        fn_len = struct.unpack(">I", all_raw_bytes[4:8])[0]
        fn = all_raw_bytes[8:8+fn_len].decode('utf-8', errors='ignore')
        payload_len = struct.unpack(">Q", all_raw_bytes[8+fn_len:8+fn_len+8])[0]
        start_idx = 8 + fn_len + 8
        end_idx = start_idx + payload_len
        payload = all_raw_bytes[start_idx:end_idx]
        return {"filename": fn, "data": payload, "is_encrypted": False}

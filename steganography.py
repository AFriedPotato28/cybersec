import cv2, numpy as np
import wave
import math

METADATA_MESSAGE_LENGTH_SIZE = 32
METADATA_FILE_TYPE_SIZE = 24
METADATA_LENGTH = METADATA_MESSAGE_LENGTH_SIZE + METADATA_FILE_TYPE_SIZE


def encode(cover_path: str, payload_path: str, bits: int, output_path: str):
    file_extension = cover_path.split(".")[-1].lower()
    payload_extension = payload_path.split(".")[-1].lower()

    if file_extension in ["png", "bmp"]:
        cover_data = cv2.imread(cover_path)
        payload_data = read_file(payload_path)

        encoded_image = encode_image(cover_data, payload_data, bits, payload_extension)
        cv2.imwrite(output_path, encoded_image)

    elif file_extension in ["wav"]:
        w = wave.open(cover_path, "rb")
        cover_data = w.readframes(w.getnframes())
        payload_data = read_file(payload_path)
        encoded_audio = encode_audio(cover_data, payload_data, bits, payload_extension)

        with wave.open(output_path, mode="wb") as file:
            file.setnchannels(w.getnchannels())
            file.setsampwidth(w.getsampwidth())
            file.setframerate(w.getframerate())
            file.writeframes(encoded_audio)
    
    elif file_extension in ["mp4", "avi", "mov"]:
        encode_video(cover_path, payload_path, bits, output_path, payload_extension)    

    else:
        ValueError("File type unsupported")


def decode(stego_path: str, bits: int):
    file_extension = stego_path.split(".")[-1].lower()

    if file_extension in ["png", "bmp"]:
        stego_data = cv2.imread(stego_path)

        return decode_image(stego_data, bits)
    elif file_extension in ["wav"]:
        w = wave.open(stego_path, "rb")
        stego_data = w.readframes(w.getnframes())

        return decode_audio(stego_data, bits)
    
    elif file_extension in ["mp4", "avi", "mov"]:
        return decode_video(stego_path, bits)   
    else:
        ValueError("File type unsupported")


def encode_image(
    cover_data: np.ndarray, payload_data: str, bits: int, file_extension: str
):
    print("\nEncoding Image..")
    metadata = generate_metadata(payload_data, file_extension)
    payload_data = metadata + payload_data

    if not is_encodable(cover_data, payload_data, bits):
        ValueError("Cover Object size is too small")

    for row in cover_data:
        for pixel in row:
            pixel_data = to_bin(pixel)
            for index, bin_str in enumerate(pixel_data):
                if len(payload_data) > 0:
                    pixel[index] = int(bin_str[:-bits] + payload_data[0:bits], 2)
                    payload_data = payload_data[bits:]
                else:
                    print("Finished encoding Image!")
                    return cover_data


def encode_audio(
    cover_data_bytes: bytes, payload_data: str, bits: int, payload_extension: str
):
    print("\nEncoding Audio..")
    mutable_cover_data = bytearray(cover_data_bytes)  # to allow array to be editted
    metadata = generate_metadata(payload_data, payload_extension)
    payload_data = metadata + payload_data

    if not is_encodable(cover_data_bytes, payload_data, bits):
        ValueError("Cover Object size is too small")

    number_of_iterations = len(payload_data) / bits
    payload_index = 0
    for index, byte in enumerate(mutable_cover_data):
        if payload_index < len(payload_data):
            bin_str = to_bin(byte)
            mutable_cover_data[index] = int(
                bin_str[:-bits] + payload_data[payload_index : payload_index + bits], 2
            ).to_bytes(1, byteorder="big")[0]
            # payload_data = payload_data[bits:]

            payload_index += bits

            if index % math.floor(number_of_iterations / 50) == 0:
                print(
                    f"Progress: {index / number_of_iterations * 100}% || Payload Length Left: {len(payload_data)}"
                )

        else:
            print("Finished encoding Audio!")
            return mutable_cover_data


def decode_audio(stego_data: bytes, bits: int):
    print("\nDecoding Audio..")
    payload_array = []
    for index, byte in enumerate(stego_data):
        bin_str = to_bin(byte)
        payload_array.append(bin_str[-bits:])

    payload_data = "".join(payload_array)
    metadata = get_metadata(payload_data)
    print("Finished decoding Audio!")
    return metadata


def is_encodable(cover_data, payload_data: str, bits: int):
    print("\nChecking if payload is encodable..")
    if isinstance(cover_data, np.ndarray):
        cover_data = (
            cover_data.flatten()
        )  # Change the multidimensional array to just 1 dimension
    cover_data_bytes = len(cover_data)
    needed_bytes = math.ceil(len(payload_data) / bits)
    print(
        "Length of payload data: ",
        len(payload_data),
        "|| Number of bytes: ",
        len(payload_data) / 8,
        "|| Bytes needed",
        needed_bytes,
    )
    print("Cover Bytes: ", len(cover_data), "|| Bytes needed to encode: ", needed_bytes)

    # Check if the number of bytes needed to encode all the payload is smaller than the cover_data bytes
    if cover_data_bytes > needed_bytes:
        print("Payload is encodable!")
        return True
    else:
        print("Payload is NOT encodable!")
        return False


def generate_metadata(payload_data: str, payload_extension: str):
    print("\nGenerating Metadata..")
    metadata = ""
    metadata += format(len(payload_data), "032b")
    metadata += "".join(format(ord(char), "08b") for char in payload_extension)

    print("Generated Metadata", metadata, "|| Length of metadata: ", len(metadata))
    return metadata


def get_metadata(payload_data: str):
    print("\nDecoding Metadata..")
    message_length = int(payload_data[0:METADATA_MESSAGE_LENGTH_SIZE], 2)
    message_extension = bytes(
        int(payload_data[i : i + 8], 2)
        for i in range(
            METADATA_MESSAGE_LENGTH_SIZE,
            METADATA_LENGTH,
            8,
        )
    ).decode("ascii")

    bin_message = payload_data[METADATA_LENGTH : METADATA_LENGTH + message_length]
    message = bytes(
        int(bin_message[i : i + 8], 2) for i in range(0, len(bin_message), 8)
    )

    metadata = {
        "message_extension": message_extension,
        "message_length": message_length,
        "message": message,
    }

    print(
        "Decoded Metadata Length:",
        metadata["message_length"],
        "|| Metadata Extension:",
        metadata["message_extension"],
    )
    return metadata


def read_file(file_path: str):
    with open(file_path, mode="rb") as file:
        data = file.read()
        bit_string = "".join(to_bin(data))
        return bit_string


def write_file(file_path: str, binary_data: str):
    with open(file_path, "wb") as file:
        file.write(binary_data)


# COPIED FROM PROF
def to_bin(data):
    """Convert `data` to binary format as string"""
    if isinstance(data, str):
        return "".join([format(ord(i), "08b") for i in data])
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [format(i, "08b") for i in data]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, "08b")
    else:
        raise TypeError("Type not supported.")


def decode_image(stego_data: str, bits: int):
    print("\nDecoding Image..")
    payload_array = []
    payload_data = ""

    for row in stego_data:
        for pixel in row:
            pixel_data = to_bin(pixel)
            for bin in pixel_data:
                # payload_data += bin[-bits:]
                payload_array.append(bin[-bits:])

    payload_data = "".join(payload_array)
    metadata = get_metadata(payload_data)

    print("Finished decoding Image")
    return metadata


def decode_image2(stego_data: str, bits: int):
    metadata = ""
    metadata_bin = ""
    reading_metadata = True
    metadata_length = 32  # message length size
    payload_data = ""

    for row in stego_data:
        for pixel in row:
            for i in range(len(pixel)):
                pixel_bin = to_bin(pixel[i])
                if reading_metadata:
                    metadata_bin += pixel_bin[-bits]
                    if len(metadata_bin) == metadata_length:
                        metadata = get_metadata(metadata_bin)
                        payload_size = metadata["message_length"]
                        reading_metadata = False
                else:
                    payload_data += pixel_bin[-bits]
                    if len(payload_data) * bits >= payload_size:
                        payload_bits = "".join(payload_data)[:payload_size]
                        return int(payload_bits, 2).to_bytes(
                            (payload_size + 7) // 8, byteorder="big"
                        )

    raise ValueError(
        "Failed to extract payload. The image may not contain the encoded data."
    )


def compare_object(
    object_path1: str, object_path2: str, output_path: str = "compare.png"
):
    print(f"Comparing {object_path1} and {object_path2}")
    file_extension1 = object_path1.split(".")[-1].lower()
    file_extension2 = object_path2.split(".")[-1].lower()

    if file_extension1 not in ["png", "bmp"] or file_extension2 not in ["png", "bmp"]:
        ValueError("File type unsupported")

    object_data1 = cv2.imread(object_path1)
    object_data2 = cv2.imread(object_path2)

    comparison_result = object_data1.copy()
    count = 0

    for r, row in enumerate(object_data1):
        for p, pixel in enumerate(row):
            if not all(pixel == object_data2[r][p]):
                # print("not the same")
                comparison_result[r][p] = [0, 0, 255]
                count = count + 1

    print("Diff", count)
    cv2.imwrite(output_path, comparison_result)

def encode_video(cover_path: str, payload_path: str, bits: int, output_path: str, file_extension: str):
    print("\nEncoding Video..")
    cap = cv2.VideoCapture(cover_path)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, cap.get(cv2.CAP_PROP_FPS), 
                          (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))))

    payload_data = read_file(payload_path)
    metadata = generate_metadata(payload_data, file_extension)
    payload_data = metadata + payload_data
    
    if not is_encodable_video(cap, payload_data, bits):
        raise ValueError("Cover Object size is too small")

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if len(payload_data) > 0:
            encoded_frame, payload_data = encode_frame(frame, payload_data, bits)
            out.write(encoded_frame)
        else:
            out.write(frame)
        frame_count += 1

    cap.release()
    out.release()
    print("Finished encoding Video!")

def encode_frame(frame, payload_data, bits):
    for row in frame:
        for pixel in row:
            pixel_data = to_bin(pixel)
            for index, bin_str in enumerate(pixel_data):
                if len(payload_data) > 0:
                    pixel[index] = int(bin_str[:-bits] + payload_data[:bits], 2)
                    payload_data = payload_data[bits:]
                else:
                    return frame, payload_data
    return frame, payload_data


def decode_video(stego_path: str, bits: int):
    print("\nDecoding Video..")
    cap = cv2.VideoCapture(stego_path)
    payload_array = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        payload_array.append(extract_payload_from_frame(frame, bits))
    
    payload_data = "".join(payload_array)
    metadata = get_metadata(payload_data)
    cap.release()
    print("Finished decoding Video!")
    return metadata


def extract_payload_from_frame(frame, bits):
    payload_array = []
    for row in frame:
        for pixel in row:
            pixel_data = to_bin(pixel)
            for bin_str in pixel_data:
                payload_array.append(bin_str[-bits:])
    return "".join(payload_array)


def is_encodable_video(cap, payload_data, bits):
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cover_data_bytes = frame_count * frame_height * frame_width * 3  # 3 bytes per pixel (RGB)
    needed_bytes = math.ceil(len(payload_data) / bits)
    return cover_data_bytes > needed_bytes



if __name__ == "__main__":
    coverObjectPath = "./coverObject.png"
    encodedObjectPath = "./encodedObject.png"
    payloadPath = "./coverObject.png"

    # encode(coverObjectPath, payloadPath, 6, encodedObjectPath)

    # data = decode(encodedObjectPath, 6)
    # print("Decoded_message: ", data)

    # write_file(f"decodedMessage.{data["message_extension"]}", data["message"])

    compare_object(coverObjectPath, encodedObjectPath)

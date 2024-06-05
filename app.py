import base64
from flask import Flask, jsonify, render_template, request, url_for
import steganography

# Create a Flask app instance
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/encode", methods=["POST"])
def encode():
    print("Encode function called..")
    print(request.files)
    print(request.form.get("bits"))
    for key in [
        "file-payload",
        "file-cover",
    ]:  # Adjust this list based on the names of your input elements
        if key not in request.files:
            print("Error")
            return jsonify({"error": "Payload and Cover Object cannot be empty!"}), 400

    bits = request.form.get("bits")
    if bits == None:
        return jsonify({"error": "You have to choose how many bits to encode!"}), 400

    cover_file = request.files["file-cover"]
    payload_file = request.files["file-payload"]

    print(cover_file.filename)

    cover_file_name = f"./temp/cover_{cover_file.filename}"
    payload_file_name = f"./temp/payload_{payload_file.filename}"

    cover_extension = cover_file.filename.lower().split(".")[-1]
    encoded_file_path = f"./temp/encoded_{cover_file.filename}.{cover_extension}"

    cover_file.save(cover_file_name)
    payload_file.save(payload_file_name)

    print(payload_file_name, cover_file_name)
    try:
        steganography.encode(
            cover_file_name, payload_file_name, int(bits), encoded_file_path
        )
    except Exception as error:
        return jsonify({"error": str(error)}), 400

    with open(encoded_file_path, "rb") as f:
        encoded_file_content = f.read()

    encoded_file_base64 = base64.b64encode(encoded_file_content).decode("utf-8")
    download_content = f'<a href="data:application/octet-stream;base64,{encoded_file_base64}" download="encoded_file.{cover_extension}">Download Encoded File</a>'
    if cover_extension in ["png", "jpg", "jpeg", "gif"]:
        # For image files
        html_content = (
            f'<img src="data:image/{cover_extension};base64,{encoded_file_base64}" alt="Encoded Image">'
            + download_content
        )
    elif cover_extension in ["mp3", "wav"]:
        # For audio files
        html_content = (
            f'<audio controls><source src="data:audio/{cover_extension};base64,{encoded_file_base64}" type="audio/{cover_extension}">Your browser does not support the audio tag.</audio>'
            + download_content
        )
    elif cover_extension in ["mp4", "avi", "mov"]:
        # For video files
        html_content = (
            f'<video controls><source src="data:video/{cover_extension};base64,{encoded_file_base64}" type="video/{cover_extension}">Your browser does not support the video tag.</video>'
            + download_content
        )
    elif cover_extension in ["txt"]:
        html_content = (
            f'<div class="textBox">{encoded_file_content}</div>' + download_content
        )
    else:
        # For other file types, provide a download link
        html_content = download_content

    print("Encode function end.")
    return html_content


@app.route("/decode", methods=["POST"])
def decode():
    print("Decode function called..")
    print(request.files)
    for key in ["file-stego"]:  # Adjust this list based on the names of your input elements
        if key not in request.files:
            print("Error")
            return jsonify({"error": "Encoded Object cannot be empty!"}), 400

    bits = request.form.get("bits")
    if bits == None:
        return jsonify({"error": "You have to choose how many bits to encode!"}), 400

    stego_file = request.files["file-stego"]

    stego_file_name = f"./temp/stego_{stego_file.filename}"
    stego_file.save(stego_file_name)

    try:
        data = steganography.decode(stego_file_name, int(bits))
    except Exception as error:
        return jsonify({"error": str(error)}), 400

    decoded_file_path = f"./temp/decoded_{stego_file.filename}.{data['message_extension']}"

    try:
        steganography.write_file(decoded_file_path, data["message"])
    except Exception as error:
        return jsonify({"error": str(error)}), 400

    with open(decoded_file_path, "rb") as f:
        decoded_file_content = f.read()

    decoded_file_base64 = base64.b64encode(decoded_file_content).decode("utf-8")
    download_content = f'<a href="data:application/octet-stream;base64,{decoded_file_base64}" download="encoded_file.{data['message_extension']}">Download Encoded File</a>'
    if data['message_extension'] in ["png", "jpg", "jpeg", "gif"]:
        # For image files
        html_content = (
            f'<img src="data:image/{data['message_extension']};base64,{decoded_file_base64}" alt="Encoded Image">'
            + download_content
        )
    elif data['message_extension'] in ["mp3", "wav"]:
        # For audio files
        html_content = (
            f'<audio controls><source src="data:audio/{data["message_extension"]};base64,{decoded_file_base64}" type="audio/{data["message_extension"]}">Your browser does not support the audio tag.</audio>'
            + download_content
        )
    elif data['message_extension'] in ["mp4", "avi", "mov"]:
        # For video files
        html_content = (
            f'<video controls><source src="data:video/{data['message_extension']};base64,{decoded_file_base64}" type="video/{data['message_extension']}">Your browser does not support the video tag.</video>'
            + download_content
        )
    elif data['message_extension'] in ["txt"]:
        html_content = (
            f'<div class="textBox">{decoded_file_content}</div>' + download_content
        )
    else:
        # For other file types, provide a download link
        html_content = download_content

    print("Decode function end.")
    return html_content

@app.route("/compare", methods=["POST"])
def compare():
    print("Compare function called..")
    print(request.files)
    for key in ["file-object1", "file-object2"]:  # Adjust this list based on the names of your input elements
        if key not in request.files:
            print("Error")
            return jsonify({"error": "Compare Objects cannot be empty!"}), 400


    object_file1 = request.files["file-object1"]
    object_file2 = request.files["file-object2"]


    object_file_name1 = f"./temp/object1_{object_file1.filename}"
    object_file_name2 = f"./temp/object2_{object_file2.filename}"

    object_file1.save(object_file_name1)
    object_file2.save(object_file_name2)

    compare_path = "./temp/compare.png"

    try:
        steganography.compare_object(object_file_name1,object_file_name2, compare_path)
    except Exception as error:
        return jsonify({"error": str(error)}), 400

    with open(compare_path, "rb") as f:
        compare_file_content = f.read()

    compare_file_base64 = base64.b64encode(compare_file_content).decode("utf-8")
    download_content = f'<a href="data:application/octet-stream;base64,{compare_file_base64}" download="{compare_path}">Download Compared File</a>'
    
    html_content = (
            f'<img src="data:image/png;base64,{compare_file_base64}" alt="Compared Image">'
            + download_content
        )

    print("Compare function end.")
    return html_content


# Run the app
if __name__ == "__main__":
    app.run(debug=True, port=8000)

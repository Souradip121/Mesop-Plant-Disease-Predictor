import mesop as me
import base64
import requests
from PIL import Image
from io import BytesIO

# OpenAI API Key
api_key = ""

@me.stateclass
class State:
    file: me.UploadedFile
    disease_info: str = ""

def resize_image(image_data: bytes, size=(224, 224)) -> bytes:
    image = Image.open(BytesIO(image_data))
    resized_image = image.resize(size)
    byte_arr = BytesIO()
    resized_image.save(byte_arr, format=image.format)
    return byte_arr.getvalue()

def encode_image(file: me.UploadedFile) -> str:
    resized_image_data = resize_image(file.getvalue())
    return base64.b64encode(resized_image_data).decode('utf-8')

def analyze_image(file: me.UploadedFile) -> str:
    base64_image = encode_image(file)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a plant doctor. You have been given an image of a plant. Analyze the image and provide information about the disease. Also provide medication and treatment options."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    result = response.json()
    disease_info = result.get('choices', [{}])[0].get('message', {}).get('content', "Unable to analyze the image.")
    
    return disease_info

def handle_upload(event: me.UploadEvent):
    state = me.state(State)
    state.file = event.file
    state.disease_info = analyze_image(event.file)

@me.page(
    security_policy=me.SecurityPolicy(
        allowed_iframe_parents=["https://google.github.io"]
    ),
    path="/uploader",
)
def app():
    s = me.state(State)

    with me.box(
        style=me.Style(
            display="flex",
            flex_direction="column",
            align_items="center",
            justify_content="center",
            height="100vh",
            background="white",
        )
    ):
        me.text("Plant Disease Predictor", style=me.Style(font_size=24, margin=me.Margin(bottom=16)))

        with me.box(
            style=me.Style(
                background="white",
                padding=me.Padding.all(16),
                margin=me.Margin.symmetric(vertical=24, horizontal=12),
                border=me.Border.all(me.BorderSide(width=2, color="gray", style="solid")),
                border_radius=10,
                width="300px",
            )
        ):
            with me.box(style=me.Style(padding=me.Padding.all(15))):
                me.uploader(
                    label="Upload Image",
                    accepted_file_types=["image/jpeg", "image/png"],
                    on_upload=handle_upload,
                    type="flat",
                    color="primary",
                    style=me.Style(font_weight="bold"),
                )
            if s.file.size:
                with me.box(style=me.Style(margin=me.Margin.all(10))):
                    me.text(f"File name: {s.file.name}")
                    me.text(f"File size: {s.file.size}")
                    me.text(f"File type: {s.file.mime_type}")

                with me.box(style=me.Style(margin=me.Margin.all(10))):
                    me.image(src=_convert_contents_data_url(s.file))

                if s.disease_info:
                    me.text("Disease Information:")
                    me.text(s.disease_info, style=me.Style(margin=me.Margin(top=16)))

def _convert_contents_data_url(file: me.UploadedFile) -> str:
    resized_image_data = resize_image(file.getvalue())
    return (
        f"data:{file.mime_type};base64,{base64.b64encode(resized_image_data).decode()}"
    )
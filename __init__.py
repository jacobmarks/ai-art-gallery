"""AI Art Gallery plugin.

| Copyright 2017-2023, Voxel51, Inc.
| `voxel51.com <https://voxel51.com/>`_
|
"""

from datetime import datetime
import os
import uuid
from importlib.util import find_spec

import fiftyone.operators as foo
from fiftyone.operators import types
import fiftyone as fo
import fiftyone.core.utils as fou

import requests

openai = fou.lazy_import("openai")
replicate = fou.lazy_import("replicate")

SD_MODEL_URL = "stability-ai/stable-diffusion:27b93a2413e7f36cd83da926f3656280b2931564ff050bf9575f1fdf9bcd7478"
SD_SCHEDULER_CHOICES = (
    "DDIM",
    "K_EULER",
    "K_EULER_ANCESTRAL",
    "PNDM",
    "K-LMS",
)
SD_SIZE_CHOICES = (
    "128",
    "256",
    "384",
    "512",
    "576",
    "640",
    "704",
    "768",
    "832",
    "896",
    "960",
    "1024",
)

SDXL_MODEL_URL = "stability-ai/sdxl:c221b2b8ef527988fb59bf24a8b97c4561f1c671f73bd389f866bfb27c061316"
SDXL_SCHEDULER_CHOICES = (
    "DDIM",
    "K_EULER",
    "K_EULER_ANCESTRAL",
    "PNDM",
    "DPMSolverMultistep",
    "KarrasDPM",
    "HeunDiscrete",
)

SDXL_REFINE_CHOICES = ("None", "Expert Ensemble", "Base")

SDXL_REFINE_MAP = {
    "None": "no_refiner",
    "Expert Ensemble": "expert_ensemble_refiner",
    "Base": "base_image_refiner",
}

SSD1B_MODEL_URL = "lucataco/ssd-1b:1ee85ef681d5ad3d6870b9da1a4543cb3ad702d036fa5b5210f133b83b05a780"
SSD1B_SCHEDULER_CHOICES = (
    "DDIM",
    "DDPMSolverMultistep",
    "HeunDiscrete",
    "KarrasDPM",
    "K_EULER_ANCESTRAL",
    "K_EULER",
    "PNDM",
)

LC_MODEL_URL = "luosiallen/latent-consistency-model:553803fd018b3cf875a8bc774c99da9b33f36647badfd88a6eec90d61c5f62fc"

VQGAN_MODEL_URL = "mehdidc/feed_forward_vqgan_clip:28b5242dadb5503688e17738aaee48f5f7f5c0b6e56493d7cf55f74d02f144d8"

DALLE2_SIZE_CHOICES = ("256x256", "512x512", "1024x1024")

DALLE3_SIZE_CHOICES = ("1024x1024", "1024x1792", "1792x1024")

DALLE3_QUALITY_CHOICES = ("standard", "hd")


def allows_replicate_models():
    """Returns whether the current environment allows replicate models."""
    return (
        find_spec("replicate") is not None
        and "REPLICATE_API_TOKEN" in os.environ
    )


def allows_openai_models():
    """Returns whether the current environment allows openai models."""
    return find_spec("openai") is not None and "OPENAI_API_KEY" in os.environ


def download_image(image_url, filename):
    img_data = requests.get(image_url).content
    with open(filename, "wb") as handler:
        handler.write(img_data)


class Text2Image:
    """Wrapper for a Text2Image model."""

    def __init__(self):
        self.name = None
        self.model_name = None

    def generate_image(self, ctx):
        pass


class StableDiffusion(Text2Image):
    """Wrapper for a StableDiffusion model."""

    def __init__(self):
        super().__init__()
        self.name = "stable-diffusion"
        self.model_name = SD_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        width = int(ctx.params.get("width_choices", "None provided"))
        height = int(ctx.params.get("height_choices", "None provided"))
        inference_steps = ctx.params.get("inference_steps", "None provided")
        scheduler = ctx.params.get("scheduler_choices", "None provided")

        response = replicate.run(
            self.model_name,
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "inference_steps": inference_steps,
                "scheduler": scheduler,
            },
        )
        if type(response) == list:
            response = response[0]
        return response


class SDXL(Text2Image):
    """Wrapper for a StableDiffusion XL model."""

    def __init__(self):
        super().__init__()
        self.name = "sdxl"
        self.model_name = SDXL_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        inference_steps = ctx.params.get("inference_steps", 50.0)
        scheduler = ctx.params.get("scheduler_choices", "None provided")
        guidance_scale = ctx.params.get("guidance_scale", 7.5)
        refiner = ctx.params.get("refine_choices", SDXL_REFINE_CHOICES[0])
        refiner = SDXL_REFINE_MAP[refiner]
        refine_steps = ctx.params.get("refine_steps", None)
        negative_prompt = ctx.params.get("negative_prompt", None)
        high_noise_frac = ctx.params.get("high_noise_frac", None)

        _inputs = {
            "prompt": prompt,
            "inference_steps": inference_steps,
            "scheduler": scheduler,
            "refine": refiner,
            "guidance_scale": guidance_scale,
        }
        if negative_prompt is not None:
            _inputs["negative_prompt"] = negative_prompt
        if refine_steps is not None:
            _inputs["refine_steps"] = refine_steps
        if high_noise_frac is not None:
            _inputs["high_noise_frac"] = high_noise_frac

        response = replicate.run(
            self.model_name,
            input=_inputs,
        )
        if type(response) == list:
            response = response[0]
        return response


class SSD1B(Text2Image):
    """Wrapper for a SSD-1B model."""

    def __init__(self):
        super().__init__()
        self.name = "ssd-1b"
        self.model_name = SSD1B_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        inference_steps = ctx.params.get("inference_steps", 25.0)
        scheduler = ctx.params.get("scheduler_choices", "None provided")
        guidance_scale = ctx.params.get("guidance_scale", 7.5)
        negative_prompt = ctx.params.get("negative_prompt", None)

        _inputs = {
            "prompt": prompt,
            "inference_steps": inference_steps,
            "scheduler": scheduler,
            "guidance_scale": guidance_scale,
        }
        if negative_prompt is not None:
            _inputs["negative_prompt"] = negative_prompt

        response = replicate.run(
            self.model_name,
            input=_inputs,
        )
        if type(response) == list:
            response = response[0]
        return response


class LatentConsistencyModel(Text2Image):
    """Wrapper for a Latent Consistency model."""

    def __init__(self):
        super().__init__()
        self.name = "latent-consistency"
        self.model_name = LC_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        width = int(ctx.params.get("width", 768))
        height = int(ctx.params.get("height", 768))
        num_inf_steps = int(ctx.params.get("num_inference_steps", 8))
        guide_scale = float(ctx.params.get("guidance_scale", 7.5))

        response = replicate.run(
            self.model_name,
            input={
                "prompt": prompt,
                "width": width,
                "height": height,
                "num_inference_steps": num_inf_steps,
                "guidance_scale": guide_scale,
            },
        )

        if type(response) == list:
            response = response[0]
        return response


class DALLE2(Text2Image):
    """Wrapper for a DALL-E 2 model."""

    def __init__(self):
        super().__init__()
        self.name = "dalle2"

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        size = ctx.params.get("size_choices", "None provided")

        response = openai.Image.create(
            model="dall-e-2", prompt=prompt, n=1, size=size
        )
        return response["data"][0]["url"]


class DALLE3(Text2Image):
    """Wrapper for a DALL-E 3 model."""

    def __init__(self):
        super().__init__()
        self.name = "dalle3"

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        size = ctx.params.get("size_choices", "None provided")
        quality = ctx.params.get("quality_choices", "None provided")

        response = openai.Image.create(
            model="dall-e-3", prompt=prompt, n=1, quality=quality, size=size
        )
        return response["data"][0]["url"]


class VQGANCLIP(Text2Image):
    """Wrapper for a VQGAN-CLIP model."""

    def __init__(self):
        super().__init__()
        self.name = "vqgan-clip"
        self.model_name = VQGAN_MODEL_URL

    def generate_image(self, ctx):
        prompt = ctx.params.get("prompt", "None provided")
        response = replicate.run(self.model_name, input={"prompt": prompt})
        if type(response) == list:
            response = response[0]
        return response


def get_model(model_name):
    mapping = {
        "sd": StableDiffusion,
        "sdxl": SDXL,
        "ssd-1b": SSD1B,
        "latent-consistency": LatentConsistencyModel,
        "dalle2": DALLE2,
        "dalle3": DALLE3,
        "vqgan-clip": VQGANCLIP,
    }
    return mapping[model_name]()


def set_stable_diffusion_config(sample, ctx):
    sample["stable_diffusion_config"] = fo.DynamicEmbeddedDocument(
        inference_steps=ctx.params.get("inference_steps", "None provided"),
        scheduler=ctx.params.get("scheduler_choices", "None provided"),
        width=ctx.params.get("width_choices", "None provided"),
        height=ctx.params.get("height_choices", "None provided"),
    )


def set_sdxl_config(sample, ctx):
    sample["sdxl_config"] = fo.DynamicEmbeddedDocument(
        inference_steps=ctx.params.get("inference_steps", "None provided"),
        scheduler=ctx.params.get("scheduler_choices", "None provided"),
        guidance_scale=ctx.params.get("guidance_scale", 7.5),
        refiner=SDXL_REFINE_MAP[
            ctx.params.get("refine_choices", "None provided")
        ],
        refine_steps=ctx.params.get("refine_steps", None),
        negative_prompt=ctx.params.get("negative_prompt", None),
        high_noise_frac=ctx.params.get("high_noise_frac", None),
    )


def set_ssd1b_config(sample, ctx):
    sample["ssd1b_config"] = fo.DynamicEmbeddedDocument(
        inference_steps=ctx.params.get("inference_steps", "None provided"),
        scheduler=ctx.params.get("scheduler_choices", "None provided"),
        guidance_scale=ctx.params.get("guidance_scale", 7.5),
        negative_prompt=ctx.params.get("negative_prompt", None),
    )


def set_latent_consistency_config(sample, ctx):
    sample["latent_consistency_config"] = fo.DynamicEmbeddedDocument(
        inference_steps=ctx.params.get("num_inference_steps", 8),
        guidance_scale=ctx.params.get("guidance_scale", 7.5),
        width=ctx.params.get("width", 768),
        height=ctx.params.get("height", 768),
    )


def set_vqgan_clip_config(sample, ctx):
    return


def set_dalle2_config(sample, ctx):
    sample["dalle2_config"] = fo.DynamicEmbeddedDocument(
        size=ctx.params.get("size_choices", "None provided")
    )


def set_dalle3_config(sample, ctx):
    sample["dalle3_config"] = fo.DynamicEmbeddedDocument(
        size=ctx.params.get("size_choices", "None provided"),
        quality=ctx.params.get("quality_choices", "None provided"),
    )


def set_config(sample, ctx, model_name):
    mapping = {
        "sd": set_stable_diffusion_config,
        "sdxl": set_sdxl_config,
        "ssd-1b": set_ssd1b_config,
        "latent-consistency": set_latent_consistency_config,
        "dalle2": set_dalle2_config,
        "dalle3": set_dalle3_config,
        "vqgan-clip": set_vqgan_clip_config,
    }

    config_setter = mapping[model_name]
    config_setter(sample, ctx)


def generate_filepath(ctx):
    download_dir = ctx.params.get("download_dir", {})
    if type(download_dir) == dict:
        download_dir = download_dir.get("absolute_path", "/tmp")

    filename = str(uuid.uuid4())[:13].replace("-", "") + ".png"
    return os.path.join(download_dir, filename)


#### MODEL CHOICES ####
def _add_replicate_choices(model_choices):
    model_choices.add_choice("sd", label="Stable Diffusion")
    model_choices.add_choice("sdxl", label="SDXL")
    model_choices.add_choice("ssd-1b", label="SSD-1B")
    model_choices.add_choice("latent-consistency", label="Latent Consistency")
    model_choices.add_choice("vqgan-clip", label="VQGAN-CLIP")


def _add_openai_choices(model_choices):
    model_choices.add_choice("dalle2", label="DALL-E2")
    model_choices.add_choice("dalle3", label="DALL-E3")


#### STABLE DIFFUSION INPUTS ####
def _handle_stable_diffusion_input(ctx, inputs):
    size_choices = SD_SIZE_CHOICES
    width_choices = types.Dropdown(label="Width")
    for size in size_choices:
        width_choices.add_choice(size, label=size)

    inputs.enum(
        "width_choices",
        width_choices.values(),
        default="512",
        view=width_choices,
    )

    height_choices = types.Dropdown(label="Height")
    for size in size_choices:
        height_choices.add_choice(size, label=size)

    inputs.enum(
        "height_choices",
        height_choices.values(),
        default="512",
        view=height_choices,
    )

    inference_steps_slider = types.SliderView(
        label="Num Inference Steps",
        componentsProps={"slider": {"min": 1, "max": 500, "step": 1}},
    )
    inputs.int("inference_steps", default=50, view=inference_steps_slider)

    scheduler_choices_dropdown = types.Dropdown(label="Scheduler")
    for scheduler in SD_SCHEDULER_CHOICES:
        scheduler_choices_dropdown.add_choice(scheduler, label=scheduler)

    inputs.enum(
        "scheduler_choices",
        scheduler_choices_dropdown.values(),
        default="K_EULER",
        view=scheduler_choices_dropdown,
    )


#### SDXL INPUTS ####
def _handle_sdxl_input(ctx, inputs):

    inputs.str("negative_prompt", label="Negative Prompt", required=False)

    scheduler_choices_dropdown = types.Dropdown(label="Scheduler")
    for scheduler in SDXL_SCHEDULER_CHOICES:
        scheduler_choices_dropdown.add_choice(scheduler, label=scheduler)

    inputs.enum(
        "scheduler_choices",
        scheduler_choices_dropdown.values(),
        default="K_EULER",
        view=scheduler_choices_dropdown,
    )

    inference_steps_slider = types.SliderView(
        label="Num Inference Steps",
        componentsProps={"slider": {"min": 1, "max": 100, "step": 1}},
    )
    inputs.int("inference_steps", default=50, view=inference_steps_slider)

    guidance_scale_slider = types.SliderView(
        label="Guidance Scale",
        componentsProps={"slider": {"min": 0.0, "max": 10.0, "step": 0.1}},
    )
    inputs.float("guidance_scale", default=7.5, view=guidance_scale_slider)

    refiner_choices_dropdown = types.Dropdown(
        label="Refiner",
        description="Which refine style to use",
    )
    for refiner in SDXL_REFINE_CHOICES:
        refiner_choices_dropdown.add_choice(refiner, label=refiner)

    inputs.enum(
        "refine_choices",
        refiner_choices_dropdown.values(),
        default="None",
        view=refiner_choices_dropdown,
    )

    rfc = SDXL_REFINE_MAP[ctx.params.get("refine_choices", "None")]
    if rfc == "base_image_refiner":
        _default = ctx.params.get("inference_steps", 50)
        refine_steps_slider = types.SliderView(
            label="Num Refine Steps",
            componentsProps={"slider": {"min": 1, "max": _default, "step": 1}},
        )
        inputs.int(
            "refine_steps",
            label="Refine Steps",
            description="The number of steps to refine",
            default=_default,
            view=refine_steps_slider,
        )
    elif rfc == "expert_ensemble_refiner":
        inputs.float(
            "high_noise_frac",
            label="High Noise Fraction",
            description="The fraction of noise to use",
            default=0.8,
        )


#### SSD-1B INPUTS ####
def _handle_ssd1b_input(ctx, inputs):
    inputs.int("width", label="Width", default=768)
    inputs.int("height", label="Height", default=768)
    inputs.str("negative_prompt", label="Negative Prompt", required=False)

    scheduler_choices_dropdown = types.Dropdown(label="Scheduler")
    for scheduler in SSD1B_SCHEDULER_CHOICES:
        scheduler_choices_dropdown.add_choice(scheduler, label=scheduler)

    inputs.enum(
        "scheduler_choices",
        scheduler_choices_dropdown.values(),
        default="K_EULER",
        view=scheduler_choices_dropdown,
    )

    inference_steps_slider = types.SliderView(
        label="Num Inference Steps",
        componentsProps={"slider": {"min": 1, "max": 100, "step": 1}},
    )
    inputs.int("inference_steps", default=25, view=inference_steps_slider)

    guidance_scale_slider = types.SliderView(
        label="Guidance Scale",
        componentsProps={"slider": {"min": 0.0, "max": 10.0, "step": 0.1}},
    )
    inputs.float("guidance_scale", default=7.5, view=guidance_scale_slider)


#### LATENT CONSISTENCY INPUTS ####
def _handle_latent_consistency_input(ctx, inputs):

    inputs.int("width", label="Width", default=768)
    inputs.int("height", label="Height", default=768)

    inference_steps_slider = types.SliderView(
        label="Num Inference Steps",
        componentsProps={"slider": {"min": 1, "max": 50, "step": 1}},
    )
    inputs.int("num_inference_steps", default=8, view=inference_steps_slider)

    guidance_scale_slider = types.SliderView(
        label="Guidance Scale",
        componentsProps={"slider": {"min": 0.0, "max": 10.0, "step": 0.1}},
    )
    inputs.float("guidance_scale", default=7.5, view=guidance_scale_slider)


#### DALLE2 INPUTS ####
def _handle_dalle2_input(ctx, inputs):
    size_choices_dropdown = types.Dropdown(label="Size")
    for size in DALLE2_SIZE_CHOICES:
        size_choices_dropdown.add_choice(size, label=size)

    inputs.enum(
        "size_choices",
        size_choices_dropdown.values(),
        default="512x512",
        view=size_choices_dropdown,
    )


#### DALLE3 INPUTS ####
def _handle_dalle3_input(ctx, inputs):
    size_choices_dropdown = types.Dropdown(label="Size")
    for size in DALLE3_SIZE_CHOICES:
        size_choices_dropdown.add_choice(size, label=size)

    inputs.enum(
        "size_choices",
        size_choices_dropdown.values(),
        default="1024x1024",
        view=size_choices_dropdown,
    )

    quality_choices_dropdown = types.Dropdown(label="Quality")
    for quality in DALLE3_QUALITY_CHOICES:
        quality_choices_dropdown.add_choice(quality, label=quality)

    inputs.enum(
        "quality_choices",
        quality_choices_dropdown.values(),
        default="standard",
        view=quality_choices_dropdown,
    )


#### VQGAN-CLIP INPUTS ####
def _handle_vqgan_clip_input(ctx, inputs):
    return


INPUT_MAPPER = {
    "sd": _handle_stable_diffusion_input,
    "sdxl": _handle_sdxl_input,
    "ssd-1b": _handle_ssd1b_input,
    "latent-consistency": _handle_latent_consistency_input,
    "dalle2": _handle_dalle2_input,
    "dalle3": _handle_dalle3_input,
    "vqgan-clip": _handle_vqgan_clip_input,
}


def _handle_input(ctx, inputs):
    model_name = ctx.params.get("model_choices", "sd")
    model_input_handler = INPUT_MAPPER[model_name]
    model_input_handler(ctx, inputs)


def _resolve_download_dir(ctx, inputs):
    if len(ctx.dataset) == 0:
        file_explorer = types.FileExplorerView(
            choose_dir=True,
            button_label="Choose a directory...",
        )
        inputs.file(
            "download_dir",
            required=True,
            description="Choose a location to store downloaded images",
            view=file_explorer,
        )
    else:
        base_dir = os.path.dirname(ctx.dataset.first().filepath).split("/")[
            :-1
        ]
        ctx.params["download_dir"] = "/".join(base_dir)


class Txt2Image(foo.Operator):
    @property
    def config(self):
        _config = foo.OperatorConfig(
            name="txt2img",
            label="AI Art Gallery: Generate Image from Text",
            dynamic=True,
        )
        _config.icon = "/assets/icon.svg"
        return _config

    def resolve_input(self, ctx):
        inputs = types.Object()
        _resolve_download_dir(ctx, inputs)

        replicate_flag = allows_replicate_models()
        openai_flag = allows_openai_models()
        if not replicate_flag and not openai_flag:
            inputs.message(
                "message",
                label="No models available. Please set up your environment variables.",
            )
            return types.Property(inputs)

        model_choices = types.Dropdown()
        if replicate_flag:
            _add_replicate_choices(model_choices)
        if openai_flag:
            _add_openai_choices(model_choices)
        inputs.enum(
            "model_choices",
            model_choices.values(),
            default=model_choices.choices[0].value,
            label="Model",
            description="Choose a model to generate images",
            view=model_choices,
        )

        inputs.str(
            "prompt",
            label="Prompt",
            description="The prompt to generate an image from",
            required=True,
        )
        _handle_input(ctx, inputs)
        return types.Property(inputs)

    def execute(self, ctx):
        model_name = ctx.params.get("model_choices", "None provided")
        model = get_model(model_name)
        prompt = ctx.params.get("prompt", "None provided")
        image_url = model.generate_image(ctx)

        filepath = generate_filepath(ctx)
        download_image(image_url, filepath)

        sample = fo.Sample(
            filepath=filepath,
            tags=["generated"],
            model=model.name,
            prompt=prompt,
            date_created=datetime.now(),
        )
        set_config(sample, ctx, model_name)

        dataset = ctx.dataset
        dataset.add_sample(sample, dynamic=True)

        if dataset.get_dynamic_field_schema() is not None:
            dataset.add_dynamic_sample_fields()
            ctx.trigger("reload_dataset")
        else:
            ctx.trigger("reload_samples")


def register(plugin):
    plugin.register(Txt2Image)

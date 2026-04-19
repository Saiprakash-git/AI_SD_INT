import os
import io
import requests
from PIL import Image
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import warnings

warnings.filterwarnings('ignore')

processor = None
caption_model = None
ocr_reader = None

def init_multimodal_pipeline():
    global processor, caption_model, ocr_reader
    if processor is None:
        print("Loading BLIP Image Captioning Model...")
        processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        
    if ocr_reader is None:
        try:
            print("Loading EasyOCR Model...")
            import easyocr
            ocr_reader = easyocr.Reader(['en'], gpu=torch.cuda.is_available(), verbose=False)
        except Exception as e:
            print("EasyOCR failed to initialize:", e)

def extract_image_context(image_url):
    """
    Downloads an image and processes it via Image Captioning and OCR extraction.
    Returns semantic description and embedded text to bridge sensory gap for NLP.
    """
    try:
        init_multimodal_pipeline()
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        res = requests.get(image_url, headers=headers, stream=True, timeout=15)
        res.raise_for_status()
        
        image_bytes = res.content
        raw_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # 1. Image Captioning (Scene Description)
        inputs = processor(raw_image, return_tensors="pt")
        out = caption_model.generate(**inputs, max_new_tokens=50)
        caption = processor.decode(out[0], skip_special_tokens=True).strip()
        
        # 2. OCR (Embedded Text Extraction)
        ocr_text = ""
        if ocr_reader is not None:
            result = ocr_reader.readtext(image_bytes, detail=0)
            ocr_text = " ".join(result).strip()
            
        print(f"[Multi-Modal] Analyzed Media -> Caption: '{caption}' | OCR Words: {len(ocr_text.split())}")
        
        return {
            "image_url": image_url,
            "caption": caption,
            "ocr_text": ocr_text
        }
            
    except Exception as e:
        print(f"[Multi-Modal] Errored on {image_url}: {str(e)[:100]}")
        return None

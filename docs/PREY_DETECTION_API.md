# Prey Detection API Documentation

## Table of Contents
- [Overview](#overview)
  - [Detection Examples](#detection-examples)
- [Custom Models & APIs](#custom-models--apis)
- [Getting API Access](#getting-api-access)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Performance & Rate Limits](#performance--rate-limits)
- [Request Format](#request-format)
  - [Image Requirements](#image-requirements)
  - [Request Structure](#request-structure)
- [Response Format](#response-format)
- [Integration](#integration)
  - [Automatic Retry Logic](#automatic-retry-logic)
  - [Duplicate Filtering](#duplicate-filtering)
  - [Concurrency Control](#concurrency-control)
  - [Monitoring](#monitoring)
- [Usage Example](#usage-example)

The Prey Detection API is a custom-built AI service that analyzes images of cats to determine if they are carrying prey in their mouth. 

## Overview

This API uses advanced computer vision to detect prey (mice, birds, etc.) being carried by cats. It's designed to work reliably across different conditions:

- **Any cat breed or size**
- **Any environment** (indoor/outdoor)
- **Infrared images** (night vision compatible)
- **Various prey types** (rodents, birds, etc.)

### Detection Examples

<div align="center">

<table>
  <tr>
    <td align="center">
      <img src="images/day_detection.jpg" width="400" alt="Day Detection"/>
      <br/>
      <em>Daytime detection with Telegram notification</em>
    </td>
    <td align="center">
      <img src="images/night_detection.jpg" width="400" alt="Night Detection"/>
      <br/>
      <em>Night detection using infrared camera</em>
    </td>
  </tr>
</table>

</div>

The system works seamlessly in both daylight and complete darkness, thanks to the infrared camera and illumination setup.

## Custom Models & APIs

I built this API specifically for prey detection, but I can create custom models for other use cases. By using different APIs, the Raspberry Pi can monitor for virtually any event or object. 

**Have a specific use case?** Whether you need to detect different objects, behaviors, or conditions, I can build a custom model tailored to your requirements. Feel free to reach out to discuss your monitoring needs.

## Getting API Access

**Purchase API Key:**
You can purchase an API key for the Prey Detection API at:
https://buy.stripe.com/dRmaEPasU1pm3Ua6o27kc00

After purchase, you'll receive your `PREY_DETECTOR_API_KEY` credentials to configure the system.

**Legal Documents:**
Before subscribing, please review our legal policies:
- [Terms of Service](TERMS_OF_SERVICE.md) - Usage terms, subscription details, and liability
- [Privacy Policy](PRIVACY_POLICY.md) - How we handle your data and protect your privacy
- [Refund & Cancellation Policy](REFUND_CANCELLATION_POLICY.md) - Cancellation process and refund terms

By purchasing and using the API, you agree to these terms.


## Configuration

### Environment Variables

Set these variables to configure API access:

```bash
export PREY_DETECTOR_API_KEY="your_api_key_here"
```

### Performance & Rate Limits

- **Expected latency:** ~1 second (client-side full request time)
- **Maximum calls:** 1000 per day
- **Recommended:** Use SSIM filtering to reduce duplicate API calls
- **Current default:** Max 10 concurrent requests

## Request Format

### Image Requirements

- **Maximum size:** 384x384 pixels
- **Format:** JPEG
- **Encoding:** Base64 for transmission
- **Color:** RGB or grayscale (IR images supported)

The detection pipeline automatically:
1. Crops detected cat from frame
2. Resizes to 384x384 or smaller
3. Encodes as JPEG
4. Sends as base64 in API request

### Request Structure

The API endpoint is configured via environment variables:
- `api_url` - The API endpoint URL
- `PREY_DETECTOR_API_KEY` - Authentication key (sent as Bearer token)

```python
# Example request (handled automatically by the system)
POST https://prey-detection.florian-mutel.workers.dev
Headers:
  Content-Type: application/json
  Authorization: Bearer {PREY_DETECTOR_API_KEY}

Body:
{
    "image_base64": "base64_encoded_jpeg_data"
}
```

## Response Format

The API returns a simple JSON response:

```json
{
    "detected": true
}
```

- `detected` (boolean): `true` if prey is detected, `false` otherwise

## Integration

The API is integrated through the `PreyDetectorTracker` class in the classification module. The system handles:

### Automatic Retry Logic

- Retries failed requests
- Configurable retry attempts (default: 3)
- Handles transient network errors

### Duplicate Filtering

Uses SSIM (Structural Similarity Index) to avoid sending duplicate images:

```python
# In config.py -> PreyDetectorTrackerConfig
ssim_threshold: float = 0.9  # Images >90% similar are skipped
```

### Concurrency Control

```python
# In config.py -> PreyDetectorTrackerConfig
concurrency: int = 10  # Max concurrent API calls
```

### Monitoring

Check logs for API usage:

```bash
tail -f runtime/logs/main_app.log | grep "Request counter"
```

## Usage Example

For manual testing:

```python
from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey
import asyncio

async def test_detection():
    with open("cat_image.jpg", "rb") as f:
        image_bytes = f.read()
    
    result = await detect_prey(image_bytes)
    
    if result.is_positive:
        print(f"Prey detected! {result.message}")
    else:
        print("No prey detected")

asyncio.run(test_detection())
```

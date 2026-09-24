# Video Ingestion Service

## Purpose

The Video Ingestion Service is responsible for connecting to a video source and continuously providing frames to downstream AI services.

## Supported Sources

- Webcam
- Video File
- RTSP Camera

## Responsibilities

- Open the video source
- Read frames
- Monitor stream status
- Handle failures
- Release resources

## Consumers

- Detection Service
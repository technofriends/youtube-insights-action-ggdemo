from flask import Blueprint, request, jsonify
from app.services.airtable_service import AirtableService
from app.services.model_service import ModelService
from app.models.payload import Payload
import logging

webhook = Blueprint('webhook', __name__)
airtable_service = AirtableService()
model_service = ModelService()

logger = logging.getLogger(__name__)

@webhook.route('/process_video', methods=['POST'])
def process_video():
    data = request.json
    payload = Payload(**data)
    
    logger.debug(f"Received payload: {payload}")
    
    if not payload.application_section:
        payload.application_section = "4-YT-Su"
    
    row = airtable_service.get_row_by_app_section(payload.application_section)
    
    if not row or not row.get('isActive'):
        logger.error(f"Invalid or inactive application section: {payload.application_section}")
        return jsonify({"error": "Invalid or inactive application section"}), 400
    
    logger.debug("Calling model_service.process_transcript")
    result = model_service.process_transcript(row, payload.video_id)
    logger.debug(f"Received result from model_service: {result}")
    
    return jsonify(result), 200
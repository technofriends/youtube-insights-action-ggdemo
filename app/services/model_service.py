import os
import logging
import tempfile
from dotenv import load_dotenv
from langchain_community.chat_models import ChatOpenAI, ChatAnthropic, ChatPerplexity
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import requests
import yt_dlp
from pydub import AudioSegment

load_dotenv()

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.model_map = {
            "OpenAI": lambda model_name: ChatOpenAI(model_name=model_name, openai_api_key=os.getenv('OPENAI_API_KEY')),
            "Anthropic": lambda model_name: ChatAnthropic(model_name=model_name, anthropic_api_key=os.getenv('ANTHROPIC_API_KEY')),
            "Groq": lambda model_name: ChatGroq(model_name=model_name, groq_api_key=os.getenv('GROQ_API_KEY')),
            "Perplexity": lambda model_name: ChatPerplexity(model_name=model_name, api_key=os.getenv('PERPLEXITY_API_KEY'))
        }
        self.groq_api_key = os.getenv('GROQ_API_KEY')

    def fetch_youtube_transcript(self, video_id):
        try:
            # Download audio using yt-dlp
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': f'/tmp/{video_id}.%(ext)s',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
            
            audio_file = f'/tmp/{video_id}.mp3'
            
            # Check file size and split if necessary
            file_size = os.path.getsize(audio_file)
            if file_size > 25 * 1024 * 1024:  # 25MB in bytes
                return self.process_large_audio(audio_file)
            else:
                return self.transcribe_audio(audio_file)
        except Exception as e:
            logger.error(f"Error fetching YouTube transcript: {str(e)}")
            return None

    def process_large_audio(self, audio_file):
        audio = AudioSegment.from_mp3(audio_file)
        chunk_length_ms = 10 * 60 * 1000  # 10 minutes
        chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
        
        transcripts = []
        for i, chunk in enumerate(chunks):
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                chunk.export(temp_file.name, format="mp3")
                transcript = self.transcribe_audio(temp_file.name)
                if transcript:
                    transcripts.append(transcript)
                os.unlink(temp_file.name)
        
        os.remove(audio_file)
        return " ".join(transcripts)

    def transcribe_audio(self, audio_file):
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
        }
        with open(audio_file, 'rb') as f:
            files = {"file": f}
            data = {"model": "whisper-large-v3"}
            response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            return response.json()['text']
        else:
            logger.error(f"Error transcribing audio: {response.text}")
            return None

    def call_models(self, model_providers, model_names, system_prompt, user_prompt, output_strategy, video_transcript):
        for provider, model_name in zip(model_providers, model_names):
            logger.debug(f"Attempting to use model: {model_name} from provider: {provider}")
            if provider in self.model_map:
                try:
                    model = self.model_map[provider](model_name)
                    
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=f"{user_prompt}\n\nTranscript:\n{video_transcript}")
                    ]
                    
                    logger.debug(f"Sending request to {provider} model: {model_name}")
                    response = model.invoke(messages)
                    logger.debug(f"Received response from {provider} model: {model_name}")
                    
                    return {
                        "result": response.content,
                        "model": f"{provider} - {model_name}"
                    }
                    
                except Exception as e:
                    logger.error(f"Error with {provider} model {model_name}: {str(e)}")
                    if output_strategy != "First Result":
                        continue
            else:
                logger.warning(f"Provider {provider} not found in model_map")
        
        logger.error("No successful response from any model")
        return {"error": "No successful response from any model"}

    def process_transcript(self, row, video_id):
        model_providers = row.get('Model Provider', [])
        model_names = row.get('Name (from Models)', [])
        system_prompt = row.get('System Prompt (from Prompt)', [''])[0]
        user_prompt = row.get('User Prompt (from Prompt)', [''])[0]
        output_strategy = row.get('Output Strategy')

        logger.debug(f"Processing transcript for video ID: {video_id}")
        video_transcript = self.fetch_youtube_transcript(video_id)
        
        if video_transcript is None:
            return {"error": "Failed to fetch video transcript"}

        logger.debug(f"Processing transcript with strategy: {output_strategy}")
        logger.debug(f"Model providers: {model_providers}")
        logger.debug(f"Model names: {model_names}")

        return self.call_models(
            model_providers,
            model_names,
            system_prompt,
            user_prompt,
            output_strategy,
            video_transcript
        )

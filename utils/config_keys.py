"""
Configuration keys constants for the Speech Assistant application.

This module defines constants for configuration keys to improve code maintainability
and prevent typos in configuration key access.
"""

# Wake word detection configuration keys
class WakeWordKeys:
    """Ключи конфигурации для детекции ключевых слов"""
    WAKE_WORD = 'wake_word'
    SAMPLE_RATE = 'sample_rate'
    CHUNK_SIZE = 'chunk_size'
    KEYWORDS = 'keywords'
    MODEL_PATH = 'model_path'
    PRE_TRIGGER_DURATION = 'pre_trigger_duration'


# Text-to-speech configuration keys
class TTSKeys:
    """Ключи конфигурации для синтеза речи"""
    ASSISTANT = 'assistant'
    TTS_SAMPLE_RATE = 'tts_sample_rate'
    TTS_SPEAKER = 'tts_speaker'
    USE_ACCENTIZER = 'use_accentizer'
    MAX_RECORDING_DURATION = 'max_recording_duration'


# Speech recognition configuration keys
class TranscriptionKeys:
    """Ключи конфигурации для распознавания речи"""
    TRANSCRIPTION = 'transcription'
    WHISPER_MODEL = 'whisper_model'
    DEVICE = 'device'
    COMPUTE_TYPE = 'compute_type'
    LANGUAGE = 'language'
    BEAM_SIZE = 'beam_size'


# Voice detection configuration keys
class VoiceDetectionKeys:
    """Ключи конфигурации для детекции голоса"""
    VOICE_DETECTION = 'voice_detection'
    PAUSE_THRESHOLD = 'pause_threshold'
    VOICE_ENERGY_THRESHOLD = 'voice_energy_threshold'
    MIN_RECORDING_DURATION = 'min_recording_duration'
    PAUSE_DETECTION_ENABLED = 'pause_detection_enabled'


# Aggregate class for easy access to all keys
class ConfigKeys:
    """Главный класс со всеми ключами конфигурации"""
    
    # Main sections
    WAKE_WORD = WakeWordKeys.WAKE_WORD
    ASSISTANT = TTSKeys.ASSISTANT
    TRANSCRIPTION = TranscriptionKeys.TRANSCRIPTION
    VOICE_DETECTION = VoiceDetectionKeys.VOICE_DETECTION
    
    # Wake word keys
    WakeWord = WakeWordKeys
    
    # TTS keys
    TTS = TTSKeys
    
    # Transcription keys
    Transcription = TranscriptionKeys
    
    # Voice detection keys
    VoiceDetection = VoiceDetectionKeys
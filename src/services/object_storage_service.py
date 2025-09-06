"""
Object storage service for durable storage of call artifacts.
Handles audio files, transcripts, and final worker profiles.
"""

import json
import uuid
from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()

class StorageConfig(BaseModel):
    """Configuration for object storage"""
    bucket_name: str
    region: str = "us-east-1"
    endpoint_url: Optional[str] = None  # For S3-compatible services
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    retention_days: int = 30

class AuditLogEntry(BaseModel):
    """Audit log entry for compliance"""
    timestamp: datetime
    phone_hash: str
    consent: bool
    agent_version: str
    call_id: str
    event_type: str  # 'call_started', 'call_completed', 'call_failed'

class WorkerProfile(BaseModel):
    """Final extracted worker profile"""
    phone_hash: str
    call_id: str
    extracted_at: datetime
    
    # Personal information
    name: Optional[str] = None
    email: Optional[str] = None
    location: Optional[str] = None
    
    # Employment history
    current_job: Optional[Dict[str, Any]] = None
    employment_history: List[Dict[str, Any]] = []
    employment_gaps: List[Dict[str, Any]] = []
    
    # Skills and qualifications
    skills: List[str] = []
    certifications: List[str] = []
    education: List[Dict[str, Any]] = []
    
    # Call metadata
    call_duration_seconds: Optional[int] = None
    adversarial_score: float = 0.0
    confidence_score: float = 0.0
    transcript_quality: str = "unknown"  # 'high', 'medium', 'low'
    
    # Compliance
    consent_given: bool = False
    data_retention_until: datetime

class LocalStorageService:
    """Local filesystem storage implementation"""
    
    def __init__(self, storage_path: str, retention_days: int = 30):
        self.storage_path = Path(storage_path)
        self.retention_days = retention_days
        self.logger = logger.bind(service="local_storage")
        
        # Create storage directories
        self.storage_path.mkdir(exist_ok=True)
        (self.storage_path / "calls" / "audio").mkdir(parents=True, exist_ok=True)
        (self.storage_path / "calls" / "transcripts").mkdir(parents=True, exist_ok=True)
        (self.storage_path / "calls" / "profiles").mkdir(parents=True, exist_ok=True)
        (self.storage_path / "audit").mkdir(parents=True, exist_ok=True)
    
    def _generate_path(self, prefix: str, call_id: str, filename: str) -> Path:
        """Generate local file path"""
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        return self.storage_path / prefix / date_prefix / call_id / filename
    
    def store_worker_profile(self, profile: WorkerProfile) -> str:
        """Store worker profile locally"""
        file_path = self._generate_path("calls/profiles", profile.call_id, "worker_profile.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(profile.model_dump_json(indent=2))
        
        self.logger.info("Stored worker profile locally", call_id=profile.call_id, path=str(file_path))
        return f"file://{file_path.absolute()}"
    
    def store_transcript(self, call_id: str, transcript_data: Dict[str, Any]) -> str:
        """Store transcript locally"""
        file_path = self._generate_path("calls/transcripts", call_id, "transcript.json")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        transcript_with_meta = {
            "call_id": call_id,
            "stored_at": datetime.now().isoformat(),
            "transcript": transcript_data
        }
        
        with open(file_path, 'w') as f:
            json.dump(transcript_with_meta, f, indent=2)
        
        self.logger.info("Stored transcript locally", call_id=call_id, path=str(file_path))
        return f"file://{file_path.absolute()}"
    
    def write_audit_log(self, entry: AuditLogEntry) -> str:
        """Write audit log locally"""
        date_str = entry.timestamp.strftime("%Y/%m/%d")
        filename = f"audit_{entry.timestamp.strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
        file_path = self.storage_path / "audit" / date_str / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(entry.model_dump_json())
        
        self.logger.info("Wrote audit log locally", path=str(file_path))
        return f"file://{file_path.absolute()}"
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for local storage"""
        try:
            # Test write access
            test_file = self.storage_path / "health_check.txt"
            test_file.write_text("health check")
            test_file.unlink()
            
            return {
                "status": "healthy",
                "storage_accessible": True,
                "storage_path": str(self.storage_path.absolute()),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "storage_accessible": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

class ObjectStorageService:
    """Service for managing object storage operations"""
    
    def __init__(self, config: StorageConfig = None, storage_type: str = "s3", local_path: str = "./storage"):
        self.storage_type = storage_type
        self.logger = logger.bind(service="object_storage")
        
        if storage_type == "local":
            self.storage = LocalStorageService(local_path, config.retention_days if config else 30)
        else:
            # S3-compatible storage
            self.config = config
            if not config:
                raise ValueError("StorageConfig required for S3 storage")
            
            try:
                session = boto3.Session(
                    aws_access_key_id=config.access_key_id,
                    aws_secret_access_key=config.secret_access_key,
                    region_name=config.region
                )
                
                self.s3_client = session.client(
                    's3',
                    endpoint_url=config.endpoint_url
                )
                
                # Test connection
                self._ensure_bucket_exists()
                
            except (ClientError, NoCredentialsError) as e:
                self.logger.error("Failed to initialize S3 client", error=str(e))
                raise
    
    # Delegation methods - route to appropriate storage backend
    
    def store_worker_profile(self, profile: WorkerProfile) -> str:
        """Store worker profile"""
        if self.storage_type == "local":
            return self.storage.store_worker_profile(profile)
        else:
            return self._store_worker_profile_s3(profile)
    
    def store_transcript(self, call_id: str, transcript_data: Dict[str, Any]) -> str:
        """Store transcript"""
        if self.storage_type == "local":
            return self.storage.store_transcript(call_id, transcript_data)
        else:
            return self._store_transcript_s3(call_id, transcript_data)
    
    def write_audit_log(self, entry: AuditLogEntry) -> str:
        """Write audit log"""
        if self.storage_type == "local":
            return self.storage.write_audit_log(entry)
        else:
            return self._write_audit_log_s3(entry)
    
    def health_check(self) -> Dict[str, Any]:
        """Health check"""
        if self.storage_type == "local":
            return self.storage.health_check()
        else:
            return self._health_check_s3()
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        if self.storage_type == "local":
            return {
                "storage_type": "local",
                "storage_path": str(self.storage.storage_path.absolute()),
                "retention_days": self.storage.retention_days,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return self._get_storage_stats_s3()
    
    # S3-specific methods (renamed to avoid conflicts)
    
    def _ensure_bucket_exists(self):
        """Ensure the storage bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.config.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket doesn't exist, create it
                try:
                    if self.config.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.config.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.config.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.config.region}
                        )
                    
                    # Set lifecycle policy for automatic cleanup
                    self._set_lifecycle_policy()
                    
                    self.logger.info("Created storage bucket", bucket=self.config.bucket_name)
                except ClientError as create_error:
                    self.logger.error("Failed to create bucket", error=str(create_error))
                    raise
            else:
                raise
    
    def _set_lifecycle_policy(self):
        """Set lifecycle policy for automatic cleanup"""
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'DeleteOldCallData',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'calls/'},
                    'Expiration': {'Days': self.config.retention_days}
                },
                {
                    'ID': 'DeleteOldAuditLogs',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': 'audit/'},
                    'Expiration': {'Days': 365}  # Keep audit logs longer
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.config.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            self.logger.info("Set lifecycle policy", retention_days=self.config.retention_days)
        except ClientError as e:
            self.logger.warning("Failed to set lifecycle policy", error=str(e))
    
    def _generate_key(self, prefix: str, call_id: str, filename: str) -> str:
        """Generate S3 key for file"""
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        return f"{prefix}/{date_prefix}/{call_id}/{filename}"
    
    # Audio Storage
    
    def store_audio_file(self, call_id: str, audio_data: BinaryIO, 
                        filename: str = "recording.wav") -> str:
        """Store audio file in object storage"""
        key = self._generate_key("calls/audio", call_id, filename)
        
        try:
            self.s3_client.upload_fileobj(
                audio_data,
                self.config.bucket_name,
                key,
                ExtraArgs={
                    'ContentType': 'audio/wav',
                    'Metadata': {
                        'call_id': call_id,
                        'uploaded_at': datetime.now().isoformat()
                    }
                }
            )
            
            url = f"s3://{self.config.bucket_name}/{key}"
            self.logger.info("Stored audio file", call_id=call_id, key=key)
            return url
            
        except ClientError as e:
            self.logger.error("Failed to store audio file", call_id=call_id, error=str(e))
            raise
    
    def get_audio_url(self, call_id: str, filename: str = "recording.wav", 
                     expires_in: int = 3600) -> str:
        """Generate presigned URL for audio file"""
        key = self._generate_key("calls/audio", call_id, filename)
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.config.bucket_name, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            self.logger.error("Failed to generate audio URL", call_id=call_id, error=str(e))
            raise
    
    # S3-specific implementations
    
    def _store_transcript_s3(self, call_id: str, transcript_data: Dict[str, Any]) -> str:
        """Store transcript JSON in S3"""
        key = self._generate_key("calls/transcripts", call_id, "transcript.json")
        
        # Add metadata
        transcript_with_meta = {
            "call_id": call_id,
            "stored_at": datetime.now().isoformat(),
            "transcript": transcript_data
        }
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=key,
                Body=json.dumps(transcript_with_meta, indent=2),
                ContentType='application/json',
                Metadata={
                    'call_id': call_id,
                    'type': 'transcript'
                }
            )
            
            url = f"s3://{self.config.bucket_name}/{key}"
            self.logger.info("Stored transcript", call_id=call_id, key=key)
            return url
            
        except ClientError as e:
            self.logger.error("Failed to store transcript", call_id=call_id, error=str(e))
            raise
    
    def _store_worker_profile_s3(self, profile: WorkerProfile) -> str:
        """Store final worker profile JSON in S3"""
        key = self._generate_key("calls/profiles", profile.call_id, "worker_profile.json")
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=key,
                Body=profile.model_dump_json(indent=2),
                ContentType='application/json',
                Metadata={
                    'call_id': profile.call_id,
                    'phone_hash': profile.phone_hash,
                    'type': 'worker_profile',
                    'extracted_at': profile.extracted_at.isoformat()
                }
            )
            
            url = f"s3://{self.config.bucket_name}/{key}"
            self.logger.info("Stored worker profile", call_id=profile.call_id, key=key)
            return url
            
        except ClientError as e:
            self.logger.error("Failed to store worker profile", 
                            call_id=profile.call_id, error=str(e))
            raise
    
    def _write_audit_log_s3(self, entry: AuditLogEntry) -> str:
        """Write audit log entry to S3"""
        date_str = entry.timestamp.strftime("%Y/%m/%d")
        filename = f"audit_{entry.timestamp.strftime('%H%M%S')}_{uuid.uuid4().hex[:8]}.json"
        key = f"audit/{date_str}/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=key,
                Body=entry.model_dump_json(),
                ContentType='application/json',
                Metadata={
                    'type': 'audit_log',
                    'phone_hash': entry.phone_hash,
                    'event_type': entry.event_type
                }
            )
            
            url = f"s3://{self.config.bucket_name}/{key}"
            self.logger.info("Wrote audit log", phone_hash=entry.phone_hash, 
                           event_type=entry.event_type)
            return url
            
        except ClientError as e:
            self.logger.error("Failed to write audit log", error=str(e))
            raise
    
    def _health_check_s3(self) -> Dict[str, Any]:
        """Perform health check on S3 storage"""
        try:
            # Test basic operations
            test_key = f"health_check_{uuid.uuid4().hex[:8]}.txt"
            test_content = "health check"
            
            # Upload test file
            self.s3_client.put_object(
                Bucket=self.config.bucket_name,
                Key=test_key,
                Body=test_content
            )
            
            # Download test file
            response = self.s3_client.get_object(
                Bucket=self.config.bucket_name,
                Key=test_key
            )
            
            downloaded_content = response['Body'].read().decode()
            
            # Delete test file
            self.s3_client.delete_object(
                Bucket=self.config.bucket_name,
                Key=test_key
            )
            
            success = downloaded_content == test_content
            
            return {
                "status": "healthy" if success else "unhealthy",
                "bucket_accessible": True,
                "read_write_test": success,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Object storage health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "bucket_accessible": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_storage_stats_s3(self) -> Dict[str, Any]:
        """Get S3 storage statistics"""
        try:
            stats = {
                "storage_type": "s3",
                "bucket_name": self.config.bucket_name,
                "retention_days": self.config.retention_days,
                "object_counts": {"audio": 0, "transcripts": 0, "profiles": 0, "audit": 0},
                "total_size_bytes": 0
            }
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=self.config.bucket_name):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    stats["total_size_bytes"] += obj['Size']
                    
                    if obj['Key'].startswith('calls/audio'):
                        stats["object_counts"]["audio"] += 1
                    elif obj['Key'].startswith('calls/transcripts'):
                        stats["object_counts"]["transcripts"] += 1
                    elif obj['Key'].startswith('calls/profiles'):
                        stats["object_counts"]["profiles"] += 1
                    elif obj['Key'].startswith('audit'):
                        stats["object_counts"]["audit"] += 1
            
            return stats
            
        except ClientError as e:
            self.logger.error("Failed to get storage stats", error=str(e))
            raise

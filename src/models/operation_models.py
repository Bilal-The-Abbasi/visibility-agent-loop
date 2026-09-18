"""
Operation and Implementation Models for Operator Agent
"""
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field


class GeneratedArtifact(BaseModel):
    name: str
    file_path: str
    artifact_type: Literal[
        "json_ld",
        "llms_txt",
        "faq_html",
        "meta_tags",
        "robots_txt",
        "content_markdown",
        "task_ticket"
    ]
    description: str
    content: str


class OperationTask(BaseModel):
    id: str
    title: str
    assignee_role: str
    estimated_effort_hours: float
    instructions: str
    verification_step: str


class OperationResult(BaseModel):
    target: str
    created_at: str
    summary: str
    artifacts: List[GeneratedArtifact] = Field(default_factory=list)
    task_checklist: List[OperationTask] = Field(default_factory=list)
    execution_status: Literal["success", "partial", "simulated"] = "success"

    def get_artifact_by_type(self, artifact_type: str) -> Optional[GeneratedArtifact]:
        for a in self.artifacts:
            if a.artifact_type == artifact_type:
                return a
        return None

"""Shared Pydantic base models for HTTP API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ApiRequest(BaseModel):
    """Base for request bodies — rejects unknown fields to catch typos early."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ApiResponse(BaseModel):
    """Base for response bodies — ignores unknown fields for forward compatibility."""

    model_config = ConfigDict(extra="ignore", frozen=True)
